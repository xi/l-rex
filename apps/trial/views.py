from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views import generic

from apps.contrib import views as contrib_views
from apps.study import models as study_models
from apps.study import views as study_views

from . import forms
from . import models


class TrialMixin:
    trial_object = None
    slug_url_kwarg = 'trial_slug'

    @property
    def study(self):
        return self.trial.questionnaire.study

    @property
    def trial(self):
        if not self.trial_object:
            trial_slug = self.kwargs['trial_slug']
            self.trial_object = models.Trial.objects.get(slug=trial_slug)
        return self.trial_object


class TrialObjectMixin(TrialMixin):

    @property
    def trial(self):
        if not self.trial_object:
            self.trial_object =  self.get_object()
        return self.trial_object


class QuestionnaireListView(LoginRequiredMixin, study_views.StudyMixin, study_views.NextStepsMixin, generic.ListView):
    model = models.Questionnaire
    title = 'Questionnaires'

    def dispatch(self, *args, **kwargs):
        self.blocks = self.study.item_blocks
        return super().dispatch(*args, **kwargs)

    def _create_default_questionnaire_block(self, randomization):
        models.QuestionnaireBlock.objects.filter(study=self.study).delete()
        models.QuestionnaireBlock.objects.create(
            study=self.study,
            block=self.blocks[0],
            randomization=randomization,
        )

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action', None)
        if len(self.blocks)>1:
            return redirect('questionnaire-generate',study_slug=self.study.slug)
        randomization = models.QuestionnaireBlock.RANDOMIZATION_TRUE if action == 'generate_random' \
            else models.QuestionnaireBlock.RANDOMIZATION_NONE
        self._create_default_questionnaire_block(randomization)
        self.study.generate_questionnaires()
        self.study.generate_questionnaire_permutations()
        self.study.randomize_questionnaire_items()
        self.study.set_progress(self.study.PROGRESS_STD_QUESTIONNARES_GENERATED)
        messages.success(request, study_views.progress_success_message(self.study.progress))
        return redirect('questionnaires',study_slug=self.study.slug)

    def get_queryset(self):
        return super().get_queryset().filter(study=self.study)

    @property
    def consider_blocks(self):
        return len(self.blocks) > 1

    def items_by_block(self):
        questionnaires = []
        for questionnaire in self.object_list:
            blocks = []
            for block_items in questionnaire.questionnaire_items_by_block().items():
                blocks.append(block_items)
            questionnaires.append((questionnaire, blocks))
        return questionnaires

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study', args=[self.study.slug])),
            ('questionnaires', ''),
        ]


class QuestionnaireGenerateView(LoginRequiredMixin, study_views.StudyMixin, generic.TemplateView):
    title = 'Generate questionnaires'
    template_name = 'lrex_contrib/crispy_formset_form.html'
    formset = None
    helper = forms.questionnaire_block_formset_helper

    def dispatch(self, *args, **kwargs):
        self.blocks = self.study.item_blocks
        return super().dispatch(*args, **kwargs)

    def _initialize_questionnaire_blocks(self):
        models.QuestionnaireBlock.objects.filter(study=self.study).delete()
        for block in self.blocks:
            models.QuestionnaireBlock.objects.create(
                study=self.study,
                block=block,
            )

    def get(self, request, *args, **kwargs):
        self._initialize_questionnaire_blocks()
        self.formset = forms.questionnaire_block_factory(len(self.blocks))(
            queryset=models.QuestionnaireBlock.objects.filter(study=self.study)
        )
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if 'submit' in request.POST:
            self.formset = forms.questionnaire_block_factory(len(self.blocks))(request.POST, request.FILES)
            if self.formset.is_valid():
                instances = self.formset.save(commit=True)
                self.study.generate_questionnaires()
                self.study.generate_questionnaire_permutations()
                self.study.randomize_questionnaire_items()
                self.study.set_progress(self.study.PROGRESS_STD_QUESTIONNARES_GENERATED)
                messages.success(request, study_views.progress_success_message(self.study.progress))
                return redirect('questionnaires', study_slug=self.study.slug)
        return super().get(request, *args, **kwargs)


class QuestionnaireBlockUpdateView(LoginRequiredMixin, study_views.StudyMixin, generic.TemplateView):
    title = 'Edit questionnaire blocks'
    template_name = 'lrex_contrib/crispy_formset_form.html'
    formset = None
    helper = forms.questionnaire_block_update_formset_helper

    def dispatch(self, *args, **kwargs):
        self.blocks = self.study.item_blocks
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.formset = forms.questionnaire_block_update_factory(len(self.blocks))(
            queryset=models.QuestionnaireBlock.objects.filter(study=self.study)
        )
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if 'submit' in request.POST:
            self.formset = forms.questionnaire_block_update_factory(len(self.blocks))(request.POST, request.FILES)
            if self.formset.is_valid():
                self.formset.save(commit=True)
                return redirect('questionnaires', study_slug=self.study.slug)
        return super().get(request, *args, **kwargs)


class TrialListView(LoginRequiredMixin, study_views.StudyMixin, generic.ListView):
    model = models.Trial
    title = 'Trials'
    paginate_by = 16

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action', None)
        if action and action == 'download_proofs':
            filename = self.study.slug + '-proofs.csv'
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
            self.study.rating_proofs_csv(response)
            return response
        return redirect('trials', study_slug=self.study.slug)

    def get_queryset(self):
        return super().get_queryset().filter(questionnaire__study=self.study)

    def show_counter(self):
        return self.study.require_participant_id

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study-run', args=[self.study.slug])),
            ('trials', ''),
        ]


class TrialCreateView(study_views.StudyMixin, generic.CreateView):
    model = models.Trial
    form_class = forms.TrialForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['study'] = self.study
        return kwargs

    def _trial_by_id(self, id):
        if id:
            try:
                return models.Trial.objects.get(questionnaire__study=self.study, id=id)
            except models.Trial.DoesNotExist:
                pass
        return None

    def form_valid(self, form):
        active_trial = self._trial_by_id(form.instance.id)
        if active_trial:
            return reverse('rating-create', args=[active_trial.slug, 0])
        form.instance.study = self.study
        form.instance.init(self.study)
        response = super().form_valid(form)
        form.instance.generate_id()
        return response

    def get_success_url(self):
        first_questionnaire_item = models.QuestionnaireItem.objects.get(
            questionnaire=self.object.questionnaire,
            number=0
        )
        questionnaire_block = models.QuestionnaireBlock.objects.get(
            study=self.study,
            block=first_questionnaire_item.item.block
        )
        if questionnaire_block.instructions:
            return reverse('rating-block-instructions', args=[self.object.slug, 0])
        return reverse('rating-create', args=[self.object.slug, 0])


class TrialDetailView(LoginRequiredMixin, TrialObjectMixin, generic.DetailView):
    model = models.Trial
    title = 'Trial overview'

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.study.title, reverse('study-run', args=[self.study.slug])),
            ('trials', reverse('trials', args=[self.study.slug])),
            (self.object.id, ''),
        ]


class TrialDeleteView(LoginRequiredMixin, TrialObjectMixin, contrib_views.DefaultDeleteView):
    model = models.Trial

    @property
    def breadcrumbs(self):
        return [
            ('studies', reverse('studies')),
            (self.object.slug, reverse('study', args=[self.object.slug])),
            ('delete', ''),
        ]

    def get_success_url(self):
        return reverse('trials', args=[self.study.slug])


class RatingCreateMixin():

    def get_next_url(self):
        trial_items = self.trial.items
        if self.num < len(trial_items) - 1:
            if trial_items[self.num].block != trial_items[self.num + 1].block:
                questionnaire_block = models.QuestionnaireBlock.objects.get(
                    study=self.study,
                    block=trial_items[self.num + 1].block
                )
                if questionnaire_block.instructions:
                    return reverse('rating-block-instructions', args=[self.trial.slug, self.num + 1])
            return reverse('rating-create', args=[self.trial.slug, self.num + 1])
        return reverse('rating-outro', args=[self.trial.slug])


class RatingCreateView(RatingCreateMixin, TrialMixin, generic.CreateView):
    model = models.Rating
    form_class = forms.RatingForm

    def _redirect_active(self, num):
        try:
            if self.trial.status == models.TrialStatus.FINISHED:
                return reverse('rating-taken', args=[self.study.slug, self.trial.slug])
            n_ratings = models.Rating.objects.filter(trial=self.trial).count()
            n_questions = self.study.question_set.count()
            if n_ratings/n_questions != num:
                return reverse('rating-create', args=[self.trial.slug, n_ratings])
        except models.Rating.DoesNotExist:
            pass
        return None

    def dispatch(self, *args, **kwargs):
        self.num = int(self.kwargs['num'])
        redirect_link = self._redirect_active(self.num)
        if not redirect_link and self.study.question_set.count() > 1:
            redirect_link = reverse('ratings-create', args=[self.study.slug, self.trial.slug, self.num])
        if redirect_link:
            return redirect(redirect_link)
        self.questionnaire_item = models.QuestionnaireItem.objects.get(
            questionnaire=self.trial.questionnaire,
            number=self.num
        )
        self.question = self.study.question_set.first()
        self.item_questions = self.questionnaire_item.item.itemquestion_set.all()
        return super().dispatch(*args, **kwargs)

    def progress(self):
        return self.num * 100 / len(self.trial.items)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['question'] = self.question
        if self.item_questions:
            kwargs['item_question'] = self.item_questions[0]
        return kwargs

    def form_valid(self, form):
        form.instance.trial = self.trial
        form.instance.questionnaire_item = self.questionnaire_item
        return super().form_valid(form)

    def get_success_url(self):
        return self.get_next_url()

    @property
    def item_question(self):
        if self.item_questions:
            return self.item_questions[0].question
        return self.question.question

    @property
    def item_legend(self):
        if self.item_questions and self.item_questions[0].legend:
            return self.item_questions[0].legend
        if self.question.legend:
            return self.question.legend
        return ''


class RatingsCreateView(RatingCreateMixin, TrialMixin, generic.TemplateView):
    model = models.Rating
    template_name = 'lrex_trial/ratings_form.html'

    formset = None
    helper = forms.rating_formset_helper

    def dispatch(self, *args, **kwargs):
        self.num = int(self.kwargs['num'])
        self.questionnaire_item = models.QuestionnaireItem.objects.get(
            questionnaire=self.trial.questionnaire,
            number=self.num
        )
        self.questions = study_models.Question.objects.filter(
            study=self.study
        )
        self.item_questions = self.questionnaire_item.item.itemquestion_set.all()
        self.formset = forms.ratingformset_factory(len(self.questions))(
            queryset=models.Rating.objects.none()
        )
        forms.customize_to_questions(self.formset, self.questions, self.item_questions)
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.formset = forms.ratingformset_factory(len(self.questions))(request.POST, request.FILES)
        forms.customize_to_questions(self.formset, self.questions, self.item_questions)
        if self.formset.is_valid():
            instances = self.formset.save(commit=False)
            if len(instances) < len(self.questions):
                self.formset._non_form_errors = \
                    self.formset.error_class(ValidationError('Please answer all questions').error_list)
            else:
                for instance in instances:
                    instance.trial = self.trial
                    instance.questionnaire_item = self.questionnaire_item
                    instance.save()
                return redirect(self.get_next_url())
        return super().get(request, *args, **kwargs)

    @property
    def progress(self):
        return self.num * 100 / len(self.trial.items)


class RatingBlockInstructionsView(TrialMixin, generic.TemplateView):
    template_name = 'lrex_trial/rating_block_instructions.html'

    def dispatch(self, *args, **kwargs):
        self.num = int(self.kwargs['num'])
        self.questionnaire_item = models.QuestionnaireItem.objects.get(
            questionnaire=self.trial.questionnaire,
            number=self.num
        )
        return super().dispatch(*args, **kwargs)

    @property
    def block_instructions(self):
        questionnaire_block = models.QuestionnaireBlock.objects.get(
            study=self.study,
            block=self.questionnaire_item.item.block
        )
        return questionnaire_block.instructions

    def progress(self):
        return self.num * 100 / len(self.trial.items)


class RatingOutroView(TrialMixin, generic.TemplateView):
    template_name = 'lrex_trial/rating_outro.html'

    def dispatch(self, *args, **kwargs):
        self.generated_rating_proof = self.trial.generate_rating_proof()
        return super().dispatch(*args, **kwargs)


class RatingTakenView(TrialMixin, generic.TemplateView):
    template_name = 'lrex_trial/rating_taken.html'


