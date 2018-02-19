from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from apps.contrib import math
from apps.experiment import models as experiment_models
from apps.item import models as item_models
from apps.trial import models as trial_models


class Study(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ITEM_TYPE = (
        ('txt', 'Text'),
    )
    item_type = models.CharField(
        max_length=3,
        choices=ITEM_TYPE,
        default='txt',
    )

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        return super().save(*args, **kwargs)

    @property
    def experiments(self):
        return self.experiment_set.all()

    @property
    def is_textitem(self):
        return self.item_type == 'txt'

    def __str__(self):
        return self.slug

    def get_absolute_url(self):
        return reverse('study', args=[self.slug])

    def _trial_count(self):
        trial_lcm = 1
        experiments = experiment_models.Experiment.objects.filter(study=self)
        for experiment in experiments:
            condition_count = len(experiment.conditions)
            trial_lcm = math.lcm(trial_lcm,  condition_count)
        return trial_lcm

    def _init_trail_lists(self):
        lists = []
        experiments = experiment_models.Experiment.objects.filter(study=self)
        for experiment in experiments:
            list = item_models.List.objects.filter(experiment=experiment).first()
            lists.append(list)
        return lists

    def _next_trail_lists(self, last_trial):
        lists = []
        last_lists = last_trial.lists
        for last_list in last_lists:
            list = last_list.next(last_list)
            lists.append(list)
        return lists

    def _create_next_trial(self, trial_num, last_trial):
        trial = trial_models.Trial.objects.create(number=trial_num, study=self)

        if trial_num == 0:
            lists = self._init_trail_lists()
        else:
            lists = self._next_trail_lists(last_trial)

        for list in lists:
            trial_models.TrialList.objects.create(trial=trial, list=list)

        return trial

    def generate_trials(self):
        trial_models.Trial.objects.filter(study=self).delete()
        trial_count = self._trial_count()
        last_trial = None
        for i in range(trial_count):
            last_trial = self._create_next_trial(i, last_trial)