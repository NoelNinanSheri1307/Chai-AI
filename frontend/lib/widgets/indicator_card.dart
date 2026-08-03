import 'package:flutter/material.dart';

import '../core/theme/app_dimensions.dart';
import '../core/theme/app_typography.dart';
import '../core/utils/context_ext.dart';
import '../core/utils/enum_present.dart';
import '../core/utils/formatters.dart';
import '../models/analysis_components.dart';
import 'app_card.dart';

/// A detected indicator card: type, severity chip, confidence, description.
class IndicatorCard extends StatelessWidget {
  final DetectedIndicator indicator;

  const IndicatorCard({super.key, required this.indicator});

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    final accent = indicator.type.severityColor(colors, indicator.severity);

    return AppCard(
      padding: const EdgeInsets.all(AppSpacing.md),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 36,
                height: 36,
                decoration: BoxDecoration(
                  color: accent.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(AppRadius.sm),
                ),
                child: Icon(indicator.type.icon, size: 18, color: accent),
              ),
              const SizedBox(width: AppSpacing.md),
              Expanded(
                child: Text(
                  indicator.type.label,
                  style: AppTypography.label(colors.textPrimary),
                ),
              ),
              _SeverityChip(severity: indicator.severity, color: accent),
            ],
          ),
          const SizedBox(height: AppSpacing.md),
          Row(
            children: [
              Expanded(
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(AppRadius.pill),
                  child: LinearProgressIndicator(
                    value: indicator.confidence,
                    minHeight: 5,
                    backgroundColor: colors.surfaceMuted,
                    valueColor: AlwaysStoppedAnimation(accent),
                  ),
                ),
              ),
              const SizedBox(width: AppSpacing.md),
              Text(
                AppFormatters.percent(indicator.confidence),
                style: AppTypography.caption(accent),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.sm),
          Text(
            indicator.description,
            style: AppTypography.caption(colors.textSecondary),
          ),
        ],
      ),
    );
  }
}

class _SeverityChip extends StatelessWidget {
  final String severity;
  final Color color;

  const _SeverityChip({required this.severity, required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.sm + 2,
        vertical: 3,
      ),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(AppRadius.pill),
      ),
      child: Text(
        severity,
        style: AppTypography.caption(color),
      ),
    );
  }
}
