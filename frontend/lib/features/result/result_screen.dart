import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_dimensions.dart';
import '../../core/theme/app_typography.dart';
import '../../core/utils/context_ext.dart';
import '../../core/utils/enum_present.dart';
import '../../core/utils/formatters.dart';
import '../../features/history/history_controller.dart';
import '../../models/analysis_result.dart';
import '../../models/history_item.dart';
import '../../navigation/app_routes.dart';
import '../../repositories/report_repository.dart';
import '../../services/share_service.dart';
import '../../widgets/app_button.dart';
import '../../widgets/app_card.dart';
import '../../widgets/confidence_ring.dart';
import '../../widgets/fade_in.dart';
import '../../widgets/indicator_card.dart';
import '../../widgets/key_value_row.dart';
import '../../widgets/score_bar.dart';
import '../../widgets/section_header.dart';
import '../../widgets/verdict_badge.dart';

class ResultScreen extends StatefulWidget {
  final ResultArgs args;

  const ResultScreen({super.key, required this.args});

  @override
  State<ResultScreen> createState() => _ResultScreenState();
}

class _ResultScreenState extends State<ResultScreen> {
  late final AnalysisResult result = widget.args.result;
  bool _saved = false;
  String? _busy;

  Future<void> _save() async {
    if (_saved) return;
    await context.read<HistoryController>().add(
          HistoryItem(
            id: result.id,
            fileName: result.fileName,
            verdict: result.verdict,
            confidence: result.confidence,
            riskLevel: result.riskLevel,
            timestamp: result.timestamp,
          ),
        );
    if (!mounted) return;
    setState(() => _saved = true);
    context.showSnack('Saved to history');
  }

  Future<void> _exportPdf() async {
    setState(() => _busy = 'export');
    try {
      final repo = context.read<ReportRepository>();
      final share = context.read<ShareService>();
      final bytes = await repo.generatePdf(result);
      await share.sharePdf(bytes, 'chai-report.pdf');
    } catch (_) {
      if (mounted) context.showSnack('Could not generate the report.');
    } finally {
      if (mounted) setState(() => _busy = null);
    }
  }

  Future<void> _share() async {
    setState(() => _busy = 'share');
    try {
      final repo = context.read<ReportRepository>();
      final share = context.read<ShareService>();
      final text = await repo.generateShareText(result);
      await share.shareText(text);
    } finally {
      if (mounted) setState(() => _busy = null);
    }
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    final verdictColor = result.verdict.color(colors);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Analysis Result'),
        actions: [
          IconButton(
            tooltip: _saved ? 'Saved' : 'Save to history',
            icon: Icon(
              _saved ? Icons.bookmark : Icons.bookmark_border,
              color: _saved ? colors.accent : null,
            ),
            onPressed: _saved ? null : _save,
          ),
          IconButton(
            tooltip: 'Export PDF',
            icon: const Icon(Icons.picture_as_pdf_outlined),
            onPressed: _busy == null ? _exportPdf : null,
          ),
          IconButton(
            tooltip: 'Share',
            icon: const Icon(Icons.share_outlined),
            onPressed: _busy == null ? _share : null,
          ),
        ],
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(AppSpacing.lg),
          children: [
            _VerdictHeader(result: result, color: verdictColor),
            const SizedBox(height: AppSpacing.lg),

            if (result.imageBytes != null || result.heatmap != null) ...[
              _HeatmapPreview(
                result: result,
                onView: () => Navigator.of(context).pushNamed(
                  AppRoutes.heatmap,
                  arguments: HeatmapArgs(result),
                ),
              ),
              const SizedBox(height: AppSpacing.lg),
            ],

            _ExplanationCard(result: result),
            const SizedBox(height: AppSpacing.lg),

            if (result.indicators.isNotEmpty) ...[
              SectionHeader(
                title: 'Detected Indicators',
                subtitle: 'Why this verdict was reached',
              ),
              const SizedBox(height: AppSpacing.md),
              for (var i = 0; i < result.indicators.length; i++)
                FadeIn(
                  delayMs: i * 70,
                  child: Padding(
                    padding: const EdgeInsets.only(bottom: AppSpacing.sm),
                    child: IndicatorCard(indicator: result.indicators[i]),
                  ),
                ),
              const SizedBox(height: AppSpacing.lg),
            ],

            SectionHeader(
              title: 'Confidence Breakdown',
              subtitle: 'Forensic signals behind the score',
            ),
            const SizedBox(height: AppSpacing.md),
            AppCard(
              child: Column(
                children: [
                  for (final score in result.scores) ScoreBar(category: score.category, value: score.value),
                ],
              ),
            ),
            const SizedBox(height: AppSpacing.lg),

            _TimelineCard(result: result),
            const SizedBox(height: AppSpacing.lg),

            _MetadataCard(result: result),
            const SizedBox(height: AppSpacing.xl),

            AppButton(
              label: _saved ? 'Saved to History' : 'Save Analysis',
              icon: _saved ? Icons.check : Icons.bookmark_border,
              variant: _saved ? AppButtonVariant.outline : AppButtonVariant.primary,
              onPressed: _saved ? null : _save,
            ),
            const SizedBox(height: AppSpacing.sm),
            Row(
              children: [
                Expanded(
                  child: AppButton(
                    label: 'Export PDF',
                    icon: Icons.picture_as_pdf_outlined,
                    variant: AppButtonVariant.outline,
                    loading: _busy == 'export',
                    onPressed: _busy == null ? _exportPdf : null,
                  ),
                ),
                const SizedBox(width: AppSpacing.md),
                Expanded(
                  child: AppButton(
                    label: 'Share',
                    icon: Icons.share_outlined,
                    variant: AppButtonVariant.outline,
                    loading: _busy == 'share',
                    onPressed: _busy == null ? _share : null,
                  ),
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.sm),
            AppButton(
              label: 'Analyze Another',
              icon: Icons.add,
              variant: AppButtonVariant.ghost,
              onPressed: () => Navigator.of(context)
                  .pushReplacementNamed(AppRoutes.upload),
            ),
          ],
        ),
      ),
    );
  }
}

class _VerdictHeader extends StatelessWidget {
  final AnalysisResult result;
  final Color color;

  const _VerdictHeader({required this.result, required this.color});

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    return FadeIn(
      child: AppCard(
        child: Column(
          children: [
            VerdictBadge(verdict: result.verdict, large: true),
            const SizedBox(height: AppSpacing.lg),
            ConfidenceRing(
              value: result.confidence,
              color: color,
              size: 200,
              centerLabel: 'confidence',
            ),
            const SizedBox(height: AppSpacing.lg),
            Text(
              result.verdict.shortSummary,
              textAlign: TextAlign.center,
              style: AppTypography.body(colors.textSecondary),
            ),
            const SizedBox(height: AppSpacing.md),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                _Chip(
                  label: 'Risk ${result.riskLevel.label}',
                  color: result.riskLevel.color(colors),
                ),
                const SizedBox(width: AppSpacing.sm),
                _Chip(
                  label: result.heatmap != null
                      ? 'Heatmap available'
                      : 'No heatmap',
                  color: colors.textSecondary,
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _Chip extends StatelessWidget {
  final String label;
  final Color color;

  const _Chip({required this.label, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.md,
        vertical: 6,
      ),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(AppRadius.pill),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Text(label, style: AppTypography.caption(color)),
    );
  }
}

class _HeatmapPreview extends StatelessWidget {
  final AnalysisResult result;
  final VoidCallback onView;

  const _HeatmapPreview({required this.result, required this.onView});

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    return FadeIn(
      child: AppCard(
        padding: EdgeInsets.zero,
        onTap: onView,
        child: ClipRRect(
          borderRadius: BorderRadius.circular(AppRadius.lg),
          child: SizedBox(
            height: 180,
            width: double.infinity,
            child: Stack(
              fit: StackFit.expand,
              children: [
                if (result.imageBytes != null)
                  Image.memory(result.imageBytes!, fit: BoxFit.cover)
                else
                  Container(
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: [
                          colors.accent.withValues(alpha: 0.18),
                          colors.surfaceMuted,
                        ],
                      ),
                    ),
                    child: Center(
                      child: Icon(Icons.image_outlined, size: 40, color: colors.textTertiary),
                    ),
                  ),
                Container(
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      begin: Alignment.topCenter,
                      end: Alignment.bottomCenter,
                      colors: [Colors.black.withValues(alpha: 0.1), Colors.black.withValues(alpha: 0.45)],
                    ),
                  ),
                ),
                Positioned(
                  left: AppSpacing.md,
                  bottom: AppSpacing.md,
                  child: Row(
                    children: [
                      Icon(Icons.local_fire_department_outlined, size: 16, color: colors.warning),
                      const SizedBox(width: 6),
                      Text(
                        'View manipulation heatmap',
                        style: AppTypography.label(colors.textPrimary),
                      ),
                    ],
                  ),
                ),
                Positioned(
                  right: AppSpacing.md,
                  bottom: AppSpacing.md,
                  child: Icon(Icons.chevron_right, color: colors.textPrimary),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _ExplanationCard extends StatelessWidget {
  final AnalysisResult result;

  const _ExplanationCard({required this.result});

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    return FadeIn(
      child: AppCard(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Explanation',
              style: AppTypography.label(colors.textTertiary),
            ),
            const SizedBox(height: AppSpacing.sm),
            Text(
              result.explanation,
              style: AppTypography.body(colors.textPrimary),
            ),
          ],
        ),
      ),
    );
  }
}

class _TimelineCard extends StatelessWidget {
  final AnalysisResult result;

  const _TimelineCard({required this.result});

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Analysis Timeline',
            style: AppTypography.title(colors.textPrimary),
          ),
          const SizedBox(height: AppSpacing.sm),
          KeyValueRow(label: 'File', value: result.fileName ?? 'Image'),
          KeyValueRow(
            label: 'Analyzed',
            value: AppFormatters.dateTime(result.timestamp),
            divider: true,
          ),
          KeyValueRow(
            label: 'Duration',
            value: AppFormatters.duration(result.analysisDuration),
            divider: true,
          ),
          KeyValueRow(
            label: 'Confidence',
            value: AppFormatters.percent(result.confidence),
          ),
        ],
      ),
    );
  }
}

class _MetadataCard extends StatelessWidget {
  final AnalysisResult result;

  const _MetadataCard({required this.result});

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Metadata',
            style: AppTypography.title(colors.textPrimary),
          ),
          const SizedBox(height: AppSpacing.sm),
          for (final entry in result.metadata.entries)
            KeyValueRow(label: entry.key, value: entry.value),
        ],
      ),
    );
  }
}
