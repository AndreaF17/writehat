import logging

from .base import *

log = logging.getLogger(__name__)


class RemediationSummaryForm(ComponentForm):
    suggestedRemediation = forms.CharField(
        label='Suggested Remediation',
        widget=forms.Textarea,
        max_length=50000,
        required=False,
    )
    field_order = [
        'name',
        'suggestedRemediation',
        'pageBreakBefore',
        'showTitle',
    ]


class Component(BaseComponent):
    default_name = 'Remediation Summary'
    formClass = RemediationSummaryForm
    fieldList = {
        'suggestedRemediation': StringField(markdown=True, templatable=True),
    }
    htmlTemplate = 'componentTemplates/RemediationSummary.html'
    iconType = 'fas fa-wrench'
    iconColor = 'var(--green)'

    def preprocess(self, context):
        context = super().preprocess(context)

        if not (context.get('suggestedRemediation', '') or '').strip():
            context['suggestedRemediation'] = '<hl green>add here your remediation plan</hl>'

        return context