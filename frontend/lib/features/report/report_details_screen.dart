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
import '../../widgets/indicator_card.dart';
import '../../widgets/key_value_row.dart';
import '../../widgets/score_bar.dart';
import '../../widgets/section_header.dart';
import '../../widgets/verdict_badge.dart';

class ReportDetailsScreen extends StatefulWidget {
  final ReportArgs args;

  const ReportDetailsScreen({super.key, required this.args});

  @override
  State<ReportDetailsScreen> createState() => _ReportDetailsScreenState();
}

class _ReportDetailsScreenState extends State<ReportDetailsScreen> {
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

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    final verdictColor = result.verdict.color(colors);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Report Details'),
        actions: [
          IconButton(
            tooltip: 'Export PDF',
            icon: const Icon(Icons.picture_as_pdf_outlined),
            onPressed: _busy == null ? _exportPdf : null,
          ),
        ],
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(AppSpacing.lg),
          children: [
            AppCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Chai AI',
                            style: AppTypography.caption(colors.textTertiary),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            'Authenticity Report',
                            style: AppTypography.title(colors.textPrimary),
                          ),
                        ],
                      ),
                      VerdictBadge(verdict: result.verdict, confidence: result.confidence),
                    ],
                  ),
                  const SizedBox(height: AppSpacing.lg),
                  Divider(color: colors.border),
                  const SizedBox(height: AppSpacing.sm),
                  KeyValueRow(label: 'Analyzed file', value: result.fileName ?? 'Image'),
                  KeyValueRow(
                    label: 'Timestamp',
                    value: AppFormatters.dateTime(result.timestamp),
                    divider: true,
                  ),
                  KeyValueRow(
                    label: 'Analysis time',
                    value: AppFormatters.duration(result.analysisDuration),
                    divider: true,
                  ),
                  KeyValueRow(
                    label: 'Risk level',
                    value: result.riskLevel.label,
                    divider: true,
                  ),
                  KeyValueRow(
                    label: 'Confidence',
                    value: AppFormatters.percent(result.confidence),
                  ),
                  const SizedBox(height: AppSpacing.sm),
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(AppSpacing.md),
                    decoration: BoxDecoration(
                      color: verdictColor.withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(AppRadius.md),
                      border: Border.all(color: verdictColor.withValues(alpha: 0.3)),
                    ),
                    child: Text(
                      result.explanation,
                      style: AppTypography.body(colors.textPrimary),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: AppSpacing.xl),

            SectionHeader(title: 'Forensic Breakdown'),
            const SizedBox(height: AppSpacing.md),
            AppCard(
              child: Column(
                children: [
                  for (final score in result.scores)
                    ScoreBar(category: score.category, value: score.value),
                ],
              ),
            ),
            const SizedBox(height: AppSpacing.xl),

            SectionHeader(
              title: 'Detected Indicators',
              subtitle: result.indicators.isEmpty
                  ? 'None above threshold'
                  : '${result.indicators.length} found',
            ),
            const SizedBox(height: AppSpacing.md),
            if (result.indicators.isEmpty)
              AppCard(
                child: Text(
                  'No indicators above the confidence threshold were detected.',
                  style: AppTypography.body(colors.textSecondary),
                ),
              )
            else
              for (final indicator in result.indicators)
                Padding(
                  padding: const EdgeInsets.only(bottom: AppSpacing.sm),
                  child: IndicatorCard(indicator: indicator),
                ),
            const SizedBox(height: AppSpacing.xl),

            SectionHeader(title: 'Evidence'),
            const SizedBox(height: AppSpacing.md),
            AppCard(
              child: Column(
                children: [
                  for (final evidence in result.evidence)
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: AppSpacing.sm),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Icon(Icons.chevron_right, size: 16, color: colors.textTertiary),
                          const SizedBox(width: AppSpacing.sm),
                          Expanded(
                            child: Text(
                              evidence,
                              style: AppTypography.body(colors.textSecondary),
                            ),
                          ),
                        ],
                      ),
                    ),
                ],
              ),
            ),
            const SizedBox(height: AppSpacing.xl),

            SectionHeader(title: 'Metadata'),
            const SizedBox(height: AppSpacing.md),
            AppCard(
              child: Column(
                children: [
                  for (final entry in result.metadata.entries)
                    KeyValueRow(label: entry.key, value: entry.value),
                ],
              ),
            ),
            const SizedBox(height: AppSpacing.xl),

            AppButton(
              label: _saved ? 'Saved to History' : 'Save Analysis',
              icon: _saved ? Icons.check : Icons.bookmark_border,
              variant: _saved ? AppButtonVariant.outline : AppButtonVariant.primary,
              onPressed: _saved ? null : _save,
            ),
            const SizedBox(height: AppSpacing.sm),
            AppButton(
              label: 'Export PDF',
              icon: Icons.picture_as_pdf_outlined,
              variant: AppButtonVariant.outline,
              loading: _busy == 'export',
              onPressed: _busy == null ? _exportPdf : null,
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
