import 'package:flutter/material.dart';

import '../../models/verdict.dart';
import '../theme/app_colors.dart';

extension VerdictX on Verdict {
  Color color(AppColors colors) {
    switch (this) {
      case Verdict.original:
        return colors.success;
      case Verdict.aiGenerated:
        return colors.danger;
    }
  }

  IconData get icon {
    switch (this) {
      case Verdict.original:
        return Icons.verified_outlined;
      case Verdict.aiGenerated:
        return Icons.smart_toy_outlined;
    }
  }

  String get summary {
    switch (this) {
      case Verdict.original:
        return 'No significant manipulation detected. The image appears authentic.';
      case Verdict.aiGenerated:
        return 'Image appears to be fully or largely AI-generated.';
    }
  }

  String get shortSummary {
    switch (this) {
      case Verdict.original:
        return 'Appears authentic';
      case Verdict.aiGenerated:
        return 'Fully AI generated';
    }
  }
}

extension RiskLevelX on RiskLevel {
  Color color(AppColors colors) {
    switch (this) {
      case RiskLevel.low:
        return colors.success;
      case RiskLevel.medium:
        return colors.warning;
      case RiskLevel.high:
        return colors.danger;
    }
  }
}

extension IndicatorTypeX on IndicatorType {
  IconData get icon {
    switch (this) {
      case IndicatorType.frequency:
        return Icons.graphic_eq;
      case IndicatorType.texture:
        return Icons.grain;
      case IndicatorType.metadata:
        return Icons.data_object;
      case IndicatorType.diffusion:
        return Icons.blur_on;
      case IndicatorType.compression:
        return Icons.photo_size_select_small;
      case IndicatorType.lighting:
        return Icons.light_mode_outlined;
    }
  }

  Color severityColor(AppColors colors, String severity) {
    switch (severity.toLowerCase()) {
      case 'strong':
        return colors.danger;
      case 'moderate':
        return colors.warning;
      default:
        return colors.info;
    }
  }
}

extension ScoreCategoryX on ScoreCategory {
  IconData get icon {
    switch (this) {
      case ScoreCategory.texture:
        return Icons.grain;
      case ScoreCategory.metadata:
        return Icons.data_object;
      case ScoreCategory.lighting:
        return Icons.light_mode_outlined;
      case ScoreCategory.frequency:
        return Icons.graphic_eq;
      case ScoreCategory.noisePattern:
        return Icons.waves;
      case ScoreCategory.compression:
        return Icons.photo_size_select_small;
      case ScoreCategory.edgeConsistency:
        return Icons.horizontal_rule;
      case ScoreCategory.colorDistribution:
        return Icons.palette_outlined;
    }
  }
}

/// Higher score = more authentic / consistent evidence.
Color scoreColor(AppColors colors, double value) {
  if (value >= 0.66) return colors.success;
  if (value >= 0.33) return colors.warning;
  return colors.danger;
}
