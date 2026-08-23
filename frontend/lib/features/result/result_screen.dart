import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_dimensions.dart';
import '../../core/theme/app_typography.dart';
import '../../core/utils/context_ext.dart';
import '../../core/utils/enum_present.dart';
import '../../core/utils/formatters.dart';
import '../../features/history/history_controller.dart';
import '../../models/analysis_components.dart';
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
            // =========================================================
            // 1. PRIMARY FEATURE: AUTHENTICITY DETECTION
            // =========================================================
            SectionHeader(
              title: 'Authenticity Detection',
              subtitle: 'Multi-source classification decision',
            ),
            const SizedBox(height: AppSpacing.md),
            _AuthenticityCard(result: result, color: verdictColor),
            const SizedBox(height: AppSpacing.lg),

            // Source Attribution / Fallback Card
            _SourceAttributionCard(provenance: result.provenance),
            const SizedBox(height: AppSpacing.xl),

            // =========================================================
            // 2. SECOND FEATURE: IMAGE INSIGHTS
            // =========================================================
            SectionHeader(
              title: 'Image Insights',
              subtitle: 'Information extracted by Chai forensic pipeline',
            ),
            const SizedBox(height: AppSpacing.xs),
            Padding(
              padding: const EdgeInsets.only(bottom: AppSpacing.md),
              child: Text(
                'Supporting image characteristics and forensic observations extracted during analysis. These signals serve as supporting context and are not standalone proof.',
                style: AppTypography.caption(colors.textTertiary),
              ),
            ),

            // Image Information (Format, Resolution, File Size, Metadata)
            _ImageInfoCard(result: result),
            const SizedBox(height: AppSpacing.lg),

            // Forensic Visualizations (Heatmap)
            if (result.imageBytes != null || result.heatmap != null) ...[
              _ForensicVisualizationCard(
                result: result,
                onView: () => Navigator.of(context).pushNamed(
                  AppRoutes.heatmap,
                  arguments: HeatmapArgs(result),
                ),
              ),
              const SizedBox(height: AppSpacing.lg),
            ],

            // Visual & Signal Analysis (Scores)
            _VisualAnalysisCard(scores: result.scores),
            const SizedBox(height: AppSpacing.lg),

            // Detected Indicators (if any)
            if (result.indicators.isNotEmpty) ...[
              SectionHeader(
                title: 'Forensic Indicators',
                subtitle: 'Specific image characteristics detected',
              ),
              const SizedBox(height: AppSpacing.md),
              for (var i = 0; i < result.indicators.length; i++)
                FadeIn(
                  delayMs: i * 60,
                  child: Padding(
                    padding: const EdgeInsets.only(bottom: AppSpacing.sm),
                    child: IndicatorCard(indicator: result.indicators[i]),
                  ),
                ),
              const SizedBox(height: AppSpacing.lg),
            ],

            // Forensic Evidence
            if (result.evidence.isNotEmpty) ...[
              _EvidenceCard(evidence: result.evidence),
              const SizedBox(height: AppSpacing.lg),
            ],

            // Detection Provenance (Expandable)
            if (result.provenance != null) ...[
              _ProvenanceCard(provenance: result.provenance!),
              const SizedBox(height: AppSpacing.xl),
            ],

            // Actions
            AppButton(
              label: _saved ? 'Saved to History' : 'Save Analysis',
              icon: _saved ? Icons.check : Icons.bookmark_border,
              variant:
                  _saved ? AppButtonVariant.outline : AppButtonVariant.primary,
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

// -----------------------------------------------------------------------------
// 1. Authenticity Detection Widgets
// -----------------------------------------------------------------------------

class _AuthenticityCard extends StatelessWidget {
  final AnalysisResult result;
  final Color color;

  const _AuthenticityCard({required this.result, required this.color});

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
              result.explanation,
              textAlign: TextAlign.center,
              style: AppTypography.body(colors.textPrimary),
            ),
            const SizedBox(height: AppSpacing.md),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                _Chip(
                  label: 'Risk: ${result.riskLevel.label}',
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

class _SourceAttributionCard extends StatelessWidget {
  final DecisionProvenance? provenance;

  const _SourceAttributionCard({this.provenance});

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    final prov = provenance;
    final isSightengineOk = prov?.isSightengineAvailable ?? false;

    if (!isSightengineOk) {
      return AppCard(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.info_outline, size: 18, color: colors.warning),
                const SizedBox(width: AppSpacing.sm),
                Text(
                  'Detection Source Notice',
                  style: AppTypography.label(colors.warning),
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.sm),
            Text(
              'External verification unavailable. Classification based on Chai forensic analysis only.',
              style: AppTypography.caption(colors.textSecondary),
            ),
            const SizedBox(height: AppSpacing.sm),
            KeyValueRow(
              label: 'Primary Detection',
              value: 'Chai Internal Forensics (100%)',
            ),
            KeyValueRow(
              label: 'Sightengine Status',
              value: prov?.sightengineStatus ?? 'Unconfigured / Offline',
              divider: true,
            ),
          ],
        ),
      );
    }

    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Text(
                  'Detection Sources',
                  style: AppTypography.label(colors.textSecondary),
                ),
              ),
              const SizedBox(width: AppSpacing.sm),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: colors.success.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(AppRadius.pill),
                ),
                child: Text(
                  '70/30 Fused',
                  style: AppTypography.caption(colors.success),
                ),
              ),
            ],
          ),

          const SizedBox(height: AppSpacing.md),
          _SourceRow(
            source: 'Sightengine',
            role: 'Primary Detection (70%)',
            status: 'Verified',
            probability: prov?.sightengineAiProbability,
            statusColor: colors.success,
          ),
          const Divider(height: AppSpacing.lg),
          _SourceRow(
            source: 'Chai AI',
            role: 'Supporting Forensic Analysis (30%)',
            status: 'Active',
            probability: prov?.chaiAiProbability,
            statusColor: colors.accent,
          ),
        ],
      ),
    );
  }
}

class _SourceRow extends StatelessWidget {
  final String source;
  final String role;
  final String status;
  final double? probability;
  final Color statusColor;

  const _SourceRow({
    required this.source,
    required this.role,
    required this.status,
    this.probability,
    required this.statusColor,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(source, style: AppTypography.label(colors.textPrimary)),
              Text(role, style: AppTypography.caption(colors.textTertiary)),
            ],
          ),
        ),
        const SizedBox(width: AppSpacing.sm),
        Column(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Text(
              status,
              style: AppTypography.caption(statusColor)
                  .copyWith(fontWeight: FontWeight.bold),
            ),
            if (probability != null)
              Text(
                'AI prob: ${(probability! * 100).round()}%',
                style: AppTypography.caption(colors.textSecondary),
              ),
          ],
        ),
      ],
    );
  }

}

// -----------------------------------------------------------------------------
// 2. Image Insights Widgets
// -----------------------------------------------------------------------------

class _ImageInfoCard extends StatelessWidget {
  final AnalysisResult result;

  const _ImageInfoCard({required this.result});

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.info_outline, size: 18, color: colors.accent),
              const SizedBox(width: AppSpacing.sm),
              Expanded(
                child: Text(
                  'Image Information',
                  style: AppTypography.title(colors.textPrimary),
                ),
              ),
            ],
          ),

          const SizedBox(height: AppSpacing.md),
          KeyValueRow(label: 'File Name', value: result.fileName ?? 'Image'),
          KeyValueRow(
            label: 'Analyzed At',
            value: AppFormatters.dateTime(result.timestamp),
            divider: true,
          ),
          KeyValueRow(
            label: 'Processing Time',
            value: AppFormatters.duration(result.analysisDuration),
            divider: true,
          ),
          for (final entry in result.metadata.entries)
            if (!entry.key.startsWith('prov:'))
              KeyValueRow(
                label: entry.key,
                value: entry.value,
                divider: true,
              ),
        ],
      ),
    );
  }
}

class _ForensicVisualizationCard extends StatelessWidget {
  final AnalysisResult result;
  final VoidCallback onView;

  const _ForensicVisualizationCard({
    required this.result,
    required this.onView,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    return FadeIn(
      child: AppCard(
        padding: EdgeInsets.zero,
        onTap: onView,
        child: ClipRRect(
          borderRadius: BorderRadius.circular(AppRadius.lg),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Padding(
                padding: const EdgeInsets.all(AppSpacing.md),
                child: Row(
                  children: [
                    Icon(Icons.remove_red_eye_outlined,
                        size: 18, color: colors.warning),
                    const SizedBox(width: AppSpacing.sm),
                    Expanded(
                      child: Text(
                        'Forensic Visualizations',
                        style: AppTypography.title(colors.textPrimary),
                      ),
                    ),
                  ],
                ),
              ),
              SizedBox(
                height: 160,
                width: double.infinity,
                child: Stack(
                  fit: StackFit.expand,
                  children: [
                    if (result.imageBytes != null)
                      Image.memory(result.imageBytes!, fit: BoxFit.cover)
                    else
                      Container(
                        color: colors.surfaceMuted,
                        child: Center(
                          child: Icon(Icons.image_outlined,
                              size: 40, color: colors.textTertiary),
                        ),
                      ),
                    Container(
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          begin: Alignment.topCenter,
                          end: Alignment.bottomCenter,
                          colors: [
                            Colors.black.withValues(alpha: 0.1),
                            Colors.black.withValues(alpha: 0.55)
                          ],
                        ),
                      ),
                    ),
                    Positioned(
                      left: AppSpacing.md,
                      bottom: AppSpacing.md,
                      child: Row(
                        children: [
                          Icon(Icons.local_fire_department_outlined,
                              size: 16, color: colors.warning),
                          const SizedBox(width: 6),
                          Text(
                            'Regions highlighted by Chai image analysis',
                            style: AppTypography.label(colors.textPrimary),
                          ),
                        ],
                      ),
                    ),
                    Positioned(
                      right: AppSpacing.md,
                      bottom: AppSpacing.md,
                      child:
                          Icon(Icons.chevron_right, color: colors.textPrimary),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _VisualAnalysisCard extends StatelessWidget {
  final List<ForensicScore> scores;

  const _VisualAnalysisCard({required this.scores});

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.analytics_outlined, size: 18, color: colors.accent),
              const SizedBox(width: AppSpacing.sm),
              Expanded(
                child: Text(
                  'Visual & Signal Analysis',
                  style: AppTypography.title(colors.textPrimary),
                ),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.xs),
          Text(
            'Internal forensic measurements across spatial frequency, lighting, and texture.',
            style: AppTypography.caption(colors.textTertiary),
          ),
          const SizedBox(height: AppSpacing.md),
          for (final score in scores)
            ScoreBar(category: score.category, value: score.value),
        ],
      ),
    );
  }
}

class _EvidenceCard extends StatelessWidget {
  final List<String> evidence;

  const _EvidenceCard({required this.evidence});

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.fact_check_outlined, size: 18, color: colors.accent),
              const SizedBox(width: AppSpacing.sm),
              Expanded(
                child: Text(
                  'Forensic Evidence',
                  style: AppTypography.title(colors.textPrimary),
                ),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.md),
          for (final item in evidence)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 4),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(Icons.chevron_right,
                      size: 16, color: colors.textTertiary),
                  const SizedBox(width: AppSpacing.sm),
                  Expanded(
                    child: Text(
                      item,
                      style: AppTypography.body(colors.textSecondary),
                    ),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }
}

class _ProvenanceCard extends StatefulWidget {
  final DecisionProvenance provenance;

  const _ProvenanceCard({required this.provenance});

  @override
  State<_ProvenanceCard> createState() => _ProvenanceCardState();
}

class _ProvenanceCardState extends State<_ProvenanceCard> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    final prov = widget.provenance;

    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          InkWell(
            onTap: () => setState(() => _expanded = !_expanded),
            borderRadius: BorderRadius.circular(AppRadius.md),
            child: Padding(
              padding: const EdgeInsets.symmetric(vertical: 4),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Row(
                      children: [
                        Icon(Icons.account_tree_outlined,
                            size: 18, color: colors.accent),
                        const SizedBox(width: AppSpacing.sm),
                        Expanded(
                          child: Text(
                            'Detection Provenance',
                            style: AppTypography.title(colors.textPrimary),
                          ),
                        ),
                      ],
                    ),
                  ),
                  Icon(
                    _expanded
                        ? Icons.keyboard_arrow_up
                        : Icons.keyboard_arrow_down,
                    color: colors.textSecondary,
                  ),
                ],
              ),
            ),
          ),

          if (_expanded) ...[
            const SizedBox(height: AppSpacing.md),
            KeyValueRow(
              label: 'Final Verdict',
              value: prov.finalClassification.label,
            ),
            KeyValueRow(
              label: 'Final Confidence',
              value: '${(prov.finalConfidence * 100).round()}%',
              divider: true,
            ),
            KeyValueRow(
              label: 'Fused AI Probability',
              value: '${(prov.finalFusedProbability * 100).toStringAsFixed(1)}%',
              divider: true,
            ),
            KeyValueRow(
              label: 'Sightengine Status',
              value: prov.sightengineStatus,
              divider: true,
            ),
            if (prov.sightengineAiProbability != null)
              KeyValueRow(
                label: 'Sightengine AI Prob',
                value:
                    '${(prov.sightengineAiProbability! * 100).toStringAsFixed(1)}%',
                divider: true,
              ),
            KeyValueRow(
              label: 'Chai Forensic Verdict',
              value: prov.chaiClassification.label,
              divider: true,
            ),
            KeyValueRow(
              label: 'Chai AI Probability',
              value: '${(prov.chaiAiProbability * 100).toStringAsFixed(1)}%',
              divider: true,
            ),
            KeyValueRow(
              label: 'Chai Edit Score',
              value: '${(prov.chaiEditScore * 100).toStringAsFixed(1)}%',
              divider: true,
            ),
            KeyValueRow(
              label: 'Fusion Weights',
              value:
                  'Sightengine: ${(prov.fusionWeightSightengine * 100).round()}% | Chai: ${(prov.fusionWeightChai * 100).round()}%',
              divider: true,
            ),
            if (prov.decisionReason.isNotEmpty) ...[
              const SizedBox(height: AppSpacing.sm),
              Text(
                'Decision Rationale:',
                style: AppTypography.caption(colors.textTertiary),
              ),
              const SizedBox(height: 2),
              Text(
                prov.decisionReason,
                style: AppTypography.body(colors.textSecondary),
              ),
            ],
          ],
        ],
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

