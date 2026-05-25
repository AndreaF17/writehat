import logging

from .base import *

log = logging.getLogger(__name__)


SECURITY_LEVEL_CHOICES = [
    ('INFO', 'INFO'),
    ('LOW', 'LOW'),
    ('MEDIUM', 'MEDIUM'),
    ('HIGH', 'HIGH'),
    ('CRITICAL', 'CRITICAL'),
]


class OverallResultsForm(ComponentForm):
    overallSecurity = forms.ChoiceField(
        label='Overall Security',
        choices=SECURITY_LEVEL_CHOICES,
        required=False,
        initial='LOW',
    )
    resultText = forms.CharField(
        label='Result Text',
        widget=forms.Textarea,
        max_length=50000,
        required=False,
    )
    limitationText = forms.CharField(
        label='Limitation Text',
        widget=forms.Textarea,
        max_length=50000,
        required=False,
    )
    field_order = [
        'name',
        'overallSecurity',
        'resultText',
        'limitationText',
        'pageBreakBefore',
        'showTitle',
    ]


class Component(BaseComponent):
    default_name = 'Overall Results'
    formClass = OverallResultsForm
    fieldList = {
        'overallSecurity': StringField(templatable=True, default='LOW'),
        'resultText': StringField(markdown=True, templatable=True),
        'limitationText': StringField(markdown=True, templatable=True),
    }
    htmlTemplate = 'componentTemplates/OverallResults.html'
    iconType = 'fas fa-shield-alt'
    iconColor = 'var(--orange)'

    @staticmethod
    def _security_markup(level):
        normalized = (level or '').strip().upper()
        color = {
            'CRITICAL': 'red',
            'HIGH': 'orange',
            'MEDIUM': 'orange',
            'LOW': 'yellow',
            'INFO': 'green',
        }.get(normalized, 'yellow')
        return f'<hl {color}>{normalized or "LOW"}</hl>'

    def preprocess(self, context):
        context = super().preprocess(context)

        customer_name = ''
        engagement = context.get('engagement')
        if engagement is not None:
            customer = getattr(engagement, 'customer', None)
            if customer is not None:
                customer_name = (getattr(customer, 'name', '') or '').strip()
            if not customer_name:
                customer_name = (getattr(engagement, 'name', '') or '').strip()

        context['overallCustomerName'] = customer_name or 'the customer'

        overall_security = (context.get('overallSecurity', 'LOW') or 'LOW').strip().upper()
        valid_levels = {choice[0] for choice in SECURITY_LEVEL_CHOICES}
        if overall_security not in valid_levels:
            overall_security = 'LOW'
        context['overallSecurity'] = overall_security
        context['overallSecurityMarkup'] = self._security_markup(overall_security)

        if not (context.get('resultText', '') or '').strip():
            context['resultText'] = (
                '<hl green>No major security problems were encountered during the activity. '
                'Add here your final overall result details.</hl>'
            )

        context['limitationText'] = (context.get('limitationText', '') or '').strip()

        return context