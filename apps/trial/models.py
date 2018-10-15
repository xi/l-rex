from collections import deque
from itertools import groupby
import random
import string
import uuid

from collections import OrderedDict
from datetime import timedelta
from enum import Enum
from django.db import models
from django.urls import reverse
from django.utils import timezone

from apps.item import models as item_models
from apps.study import models as study_models


class Questionnaire(models.Model):
    study = models.ForeignKey(
        'lrex_study.Study',
        on_delete=models.CASCADE
    )
    item_lists = models.ManyToManyField(item_models.ItemList)

    class Meta:
        ordering = ['pk']

    def get_absolute_url(self):
        return reverse('questionnaire', args=[self.study.slug, self.slug])

    @property
    def item_list_items(self):
        items = []
        for item_list in self.item_lists.all():
            items.extend(item_list.items.all())
        items_sorted = sorted(items, key=lambda i: i.block)
        return items_sorted

    @property
    def items(self):
        return [questionnaire_item.item for questionnaire_item in self.questionnaireitem_set.all()]

    @property
    def next(self):
        questionnaire =  self.study.questionnaire_set.filter(pk__gt=self.pk).first()
        if not questionnaire:
            questionnaire = Questionnaire.objects.first()
        return questionnaire

    @property
    def num(self):
        return list(Questionnaire.objects.filter(study=self.study)).index(self) + 1

    def questionnaire_items_by_block(self):
        blocks = OrderedDict()
        for questionnaire_item in self.questionnaireitem_set.all():
            if questionnaire_item.item.block in blocks:
                blocks[questionnaire_item.item.block].append(questionnaire_item)
            else:
                blocks[questionnaire_item.item.block] = [questionnaire_item]
        return blocks

    def block_items(self, block):
        return self.questionnaire_items_by_block()[block]

    def _block_randomization(self):
        block_randomization = OrderedDict()
        questionnaire_blocks = self.study.questionnaireblock_set.all()
        for questionnaire_block in questionnaire_blocks:
            block_randomization[questionnaire_block.block] = questionnaire_block.randomization
        return block_randomization

    def _generate_items_ordered(self, block_items, block_offset):
        for i, item in enumerate(block_items):
            QuestionnaireItem.objects.create(
                number=block_offset + i,
                questionnaire=self,
                item=item,
            )

    def _generate_items_random(self, block_items, block_offset):
        random.SystemRandom().shuffle(block_items)
        for i, item in enumerate(block_items):
            QuestionnaireItem.objects.create(
                number=block_offset + i,
                questionnaire=self,
                item=item,
            )

    def _experiment_items_with_alternating_conditions(self, experiment_items):
        n_tries = 100
        original_items = deque(experiment_items)
        while n_tries:
            items = original_items.copy()
            pseudo_random_items = deque()
            random.SystemRandom().shuffle(items)
            last_item = None
            bubble_fails = 0
            while bubble_fails <= len(items):
                try:
                    item = items.popleft()
                except IndexError:
                    break
                if not last_item or last_item.condition != item.condition:
                    pseudo_random_items.append(item)
                    bubble_fails = 0
                else:
                    items.append(item)
                    bubble_fails += 1
                last_item = item
            if len(items) == 0:
                if not pseudo_random_items:
                    import pdb;pdb.set_trace()
                return pseudo_random_items
            n_tries -= 1
        raise RuntimeError('Unable to compute alternating conditions')

    def _pseudo_randomized_experiment_items(self, block_items):
        items_by_experiment = {}
        for experiment, experiment_items in groupby(block_items, lambda x: x.experiment):
            if experiment.is_filler or len(experiment.conditions) == 1:
                items = list(experiment_items)
                random.SystemRandom().shuffle(items)
            else:
                items = self._experiment_items_with_alternating_conditions(experiment_items)
            items_by_experiment[experiment] = items
        return items_by_experiment


    def _generate_items_pseudo_random(self, block_items, block_offset, block_slots):
        items_by_experiment = self._pseudo_randomized_experiment_items(block_items)
        if len(block_slots) != len(block_items):
            raise RuntimeError('Block does not match master slots')
        for i, slot_experiment in enumerate(block_slots):
            item = items_by_experiment[slot_experiment].pop()
            if not item:
                raise RuntimeError('Block does not match master slots')
            QuestionnaireItem.objects.create(
                number=block_offset + i,
                questionnaire=self,
                item=item,
            )

    def _compute_block_slots(self, block_items):
        slots = []
        items = block_items.copy()
        random.SystemRandom().shuffle(items)
        colliding = []
        last_item = None
        for item in items:
            if item.experiment.is_filler \
                    or not last_item \
                    or last_item.experiment.is_filler \
                    or last_item.experiment != item.experiment:
                slots.append(item.experiment)
            else:
                colliding.append(item)
            last_item = item
        for item in colliding:
            n_tries = 100
            slot_size = len(slots)
            while n_tries:
                pos = random.SystemRandom().randint(0, slot_size - 2)
                if item.experiment != slots[pos] and item.experiment != slots[pos + 1]:
                    slots.insert(pos + 1, item.experiment)
                    break
                n_tries -= 1
            if not n_tries:
                raise RuntimeError('Unable to compute slots')
        return slots

    def _compute_slots(self):
        slots = {}
        block_randomization = self._block_randomization()
        items_by_block = groupby(self.item_list_items, lambda x: x.block)
        for block, block_items in items_by_block:
            block_items = list(block_items)
            if block_randomization[block] == QuestionnaireBlock.RANDOMIZATION_PSEUDO:
                slots[block] = self._compute_block_slots(block_items)
        return slots

    def generate_items(self):
        slots = self._compute_slots()
        block_randomization = self._block_randomization()
        items_by_block = groupby(self.item_list_items, lambda x: x.block)
        block_offset = 0
        for block, block_items in items_by_block:
            block_items = list(block_items)
            if block_randomization[block] == QuestionnaireBlock.RANDOMIZATION_TRUE:
                self._generate_items_random(block_items, block_offset)
            elif block_randomization[block] == QuestionnaireBlock.RANDOMIZATION_PSEUDO:
                self._generate_items_pseudo_random(block_items, block_offset, slots[block])
            else:
                self._generate_items_ordered(block_items, block_offset)
            block_offset += len(block_items)


class QuestionnaireBlock(models.Model):
    block = models.IntegerField()
    instructions = models.TextField(
        max_length=5000,
        help_text='These instructions will be presented to the participant before the experiment begins.',
        blank=True,
        null=True,
    )
    RANDOMIZATION_NONE = 'none'
    RANDOMIZATION_TRUE = 'true'
    RANDOMIZATION_PSEUDO = 'pseudo'
    RANDOMIZATION_TYPE = (
        (RANDOMIZATION_NONE, 'Keep item order'),
        (RANDOMIZATION_TRUE, 'Randomize'),
        (RANDOMIZATION_PSEUDO, 'Pseudo-randomize'),
    )
    randomization = models.CharField(
        max_length=8,
        choices=RANDOMIZATION_TYPE,
        default=RANDOMIZATION_TRUE,
        help_text='Randomize items in each questionnaire block',
    )
    study = models.ForeignKey(
        'lrex_study.Study',
        on_delete=models.CASCADE
    )

    class Meta:
        ordering = ['block']

    def __str__(self):
        return 'Questionnaire block {}-{}'.format(self.study, self.block)


class QuestionnaireItem(models.Model):
    number = models.IntegerField()
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE)
    item = models.ForeignKey(item_models.Item, on_delete=models.CASCADE)

    class Meta:
        ordering = ['number']


    def __str__(self):
        return '{} questionnaire {} item {}'.format(self.pk, self.questionnaire.num, self.item)


class TrialStatus(Enum):
    CREATED = 1
    STARTED = 2
    FINISHED = 3
    ABANDONED = 4


class Trial(models.Model):
    slug = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE)
    creation_date = models.DateTimeField(
        default=timezone.now
    )
    id = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text='Provide an identification number/name (as instructed by the experimenter).',
        verbose_name='ID',
    )
    rating_proof = models.CharField(
        max_length=8,
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ['creation_date']

    @property
    def items(self):
        return self.questionnaire.items

    @property
    def item_ratings(self):
        item_ratings = []
        for questionnaire_item in self.questionnaire.questionnaireitem_set.all():
            ratings = Rating.objects.filter(trial=self, questionnaire_item=questionnaire_item).all()
            item_ratings.append((questionnaire_item.item, ratings))
        return item_ratings

    @property
    def ratings_completed(self):
        n_questions = self.questionnaire.study.question_set.count()
        n_ratings = Rating.objects.filter(trial=self).count()
        return int(n_ratings / n_questions)


    @property
    def status(self):
        n_ratings = self.ratings_completed
        if n_ratings > 0:
            n_items = len(self.items)
            if n_ratings == n_items:
                return TrialStatus.FINISHED
            if self.creation_date + timedelta(1) < timezone.now():
                return TrialStatus.ABANDONED
            return TrialStatus.STARTED
        return TrialStatus.CREATED

    def init(self, study):
        last_trial = Trial.objects.filter(questionnaire__study=study).last()
        if last_trial:
            questionnaire = last_trial.questionnaire.next
        else:
            questionnaire = Questionnaire.objects.filter(study=study).first()
        self.questionnaire = questionnaire

    def generate_id(self):
        if self.id:
            return
        try:
            last_trial = Trial.objects.filter(questionnaire__study=self.questionnaire.study)\
                             .order_by('-creation_date')[1:2][0]
            self.id = int(last_trial.id) + 1
        except IndexError:
            self.id = 1
        self.save()

    def generate_rating_proof(self):
        if self.rating_proof:
            return self.rating_proof
        if self.status == TrialStatus.FINISHED:
            self.rating_proof = ''.join(
                random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(8)
            )
            self.save()
            return self.rating_proof
        return None

    def get_absolute_url(self):
        return reverse('trial', args=[self.study.slug, self.slug])

    def __str__(self):
        return 'Trial {}'.format(self.id)


class Rating(models.Model):
    trial = models.ForeignKey(Trial, on_delete=models.CASCADE)
    questionnaire_item = models.ForeignKey(QuestionnaireItem, on_delete=models.CASCADE)
    scale_value = models.ForeignKey(study_models.ScaleValue, on_delete=models.CASCADE)
