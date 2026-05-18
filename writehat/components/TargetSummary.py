import logging
from django import forms

from .base import *

log = logging.getLogger(__name__)


class TargetSummaryForm(ComponentForm):
    scores = forms.CharField(
        label='Manual Target Scores',
        required=False,
        widget=forms.Textarea(
            attrs={
                'rows': 8,
                'mde': True,
                'placeholder': (
                    'Use one target per line in this format:\n'
                    'target-name | CRITICAL\n'
                    'target-name | HIGH\n'
                    'target-name | MEDIUM\n'
                    'target-name | LOW\n'
                    'target-name | INFO\n'
                ),
            }
        ),
    )
    field_order = ['name', 'scores', 'pageBreakBefore', 'showTitle']


class Component(BaseComponent):
    default_name = 'Summary of Targets'
    htmlTemplate = 'componentTemplates/TargetSummary.html'
    fieldList = {
        'scores': StringField(default='', templatable=False),
    }
    formClass = TargetSummaryForm
    iconType = 'fas fa-bullseye'
    iconColor = 'var(--orange)'

    def set_scores_initial_from_targets(self):
        if not self.form:
            return
        target_names = self._get_target_names(self.report)
        if not target_names:
            return

        current_scores_raw = (self._model.get('scores') or '').strip()
        score_map = self._parse_scores(current_scores_raw)

        # Keep report target ordering first, then preserve any manual extra rows.
        ordered_targets = list(target_names)
        for manual_target in score_map.keys():
            if manual_target not in ordered_targets:
                ordered_targets.append(manual_target)

        changed = False
        for target in target_names:
            if target not in score_map:
                score_map[target] = 'INSERT SCORE'
                changed = True

        if not score_map:
            return

        merged_scores = '\n'.join([
            f"{target} | {(score_map.get(target) or 'INSERT SCORE').strip().upper()}"
            for target in ordered_targets
        ])

        if changed or merged_scores != current_scores_raw:
            self._model['scores'] = merged_scores
            self.form = self.formClass(initial=self.json)

    def _get_target_names(self, report):
        if report is None:
            return []

        from writehat.lib.findingGroup import BaseFindingGroup

        engagement_parent = getattr(report, 'engagementParent', None)
        fgroups = []
        if engagement_parent:
            try:
                fgroups = BaseFindingGroup.filter_children(engagementParent=engagement_parent)
                fgroups.sort(key=lambda fg: (getattr(fg, 'name', '') or '').lower())
            except Exception as e:
                log.warning(f'Failed to fetch finding groups from engagementParent: {e}')

        if not fgroups:
            fgroups = list(getattr(report, 'ordered_fgroups', []) or [])

        names = []
        seen = set()
        for fgroup in fgroups:
            target_name = (getattr(fgroup, 'name', '') or '').strip()
            if not target_name or target_name in seen:
                continue
            names.append(target_name)
            seen.add(target_name)

        return names

    @staticmethod
    def _score_markup(score):
        normalized = (score or '').strip().upper()
        color = {
            'CRITICAL': 'red',
            'HIGH': 'orange',
            'MEDIUM': 'orange',
            'LOW': 'yellow',
            'INFO': 'green',
            'INSERT SCORE': 'green',
            'TBD': 'green',
        }.get(normalized, 'green')
        return f'<hl {color}>{normalized or "INSERT SCORE"}</hl>'

    @staticmethod
    def _parse_scores(raw_scores):
        parsed = {}
        if not raw_scores:
            return parsed

        for raw_line in raw_scores.splitlines():
            line = raw_line.strip()
            if not line or line.startswith('#'):
                continue

            if '|' in line:
                target, score = line.split('|', 1)
            elif '=' in line:
                target, score = line.split('=', 1)
            else:
                continue

            target = target.strip()
            score = score.strip().upper()
            if target:
                parsed[target] = score

        return parsed

    def preprocess(self, context):
        context = super().preprocess(context)

        report = context.get('report')
        score_map = self._parse_scores(context.get('scores', ''))
        target_rows = []
        for target_name in self._get_target_names(report):
            score = score_map.get(target_name, 'INSERT SCORE')
            target_rows.append({
                'target': target_name,
                'score': score,
            })

        # If a score map exists but report has no finding groups yet,
        # still render manually provided rows.
        if not target_rows and score_map:
            for target_name, score in score_map.items():
                target_rows.append({
                    'target': target_name,
                    'score': score,
                })

        table_lines = [
            '| Targets | Criticality |',
            '| :------ | :---------: |',
        ]

        if target_rows:
            for row in target_rows:
                target = row['target'].replace('|', '\\|')
                score_markup = self._score_markup(row['score'])
                table_lines.append(f'| {target} | {score_markup} |')
        else:
            table_lines.append('| <hl green>INSERT TARGET</hl> | <hl green>INSERT SCORE</hl> |')

        context['summary_markdown'] = '\n'.join(table_lines)
        return context
