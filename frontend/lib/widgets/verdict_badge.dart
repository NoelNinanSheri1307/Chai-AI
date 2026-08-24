import 'package:flutter/material.dart';

import '../core/theme/app_dimensions.dart';
import '../core/theme/app_typography.dart';
import '../core/utils/context_ext.dart';
import '../core/utils/enum_present.dart';
import '../models/verdict.dart';

class VerdictBadge extends StatelessWidget {
  final Verdict verdict;
  final double confidence;
  final bool large;

  const VerdictBadge({
    super.key,
    required this.verdict,
    this.confidence = 0,
    this.large = false,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    final accent = verdict.color(colors);
    final radius = large ? AppRadius.pill : AppRadius.pill;

    return Container(
      padding: EdgeInsets.symmetric(
        horizontal: large ? AppSpacing.lg : AppSpacing.sm + 4,
        vertical: large ? AppSpacing.md : AppSpacing.xs + 3,
      ),
      decoration: BoxDecoration(
        color: accent.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(radius),
        border: Border.all(color: accent.withValues(alpha: 0.35)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(verdict.icon, size: large ? 22 : 15, color: accent),
          const SizedBox(width: AppSpacing.xs + 2),
          Flexible(
            child: Text(
              verdict.label,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: large
                  ? AppTypography.title(accent)
                  : AppTypography.label(accent).copyWith(fontSize: 12),
            ),
          ),
          if (confidence > 0) ...[
            const SizedBox(width: AppSpacing.xs + 2),
            Container(width: 1, height: 12, color: accent.withValues(alpha: 0.3)),
            const SizedBox(width: AppSpacing.xs + 2),
            Text(
              '${(confidence * 100).round()}%',
              style: large
                  ? AppTypography.title(accent)
                  : AppTypography.label(accent).copyWith(fontSize: 12),
            ),
          ],
        ],
      ),
    );

  }
}
