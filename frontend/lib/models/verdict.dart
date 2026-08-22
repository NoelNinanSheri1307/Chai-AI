enum Verdict {
  original,
  aiGenerated;

  String get label {
    switch (this) {
      case Verdict.original:
        return 'Real';
      case Verdict.aiGenerated:
        return 'AI Generated';
    }
  }

  static Verdict fromLabel(String label) {
    final lower = label.toLowerCase();
    if (lower == 'real' || lower == 'original') return Verdict.original;
    if (lower == 'ai generated' || lower == 'aigenerated') return Verdict.aiGenerated;
    for (final v in Verdict.values) {
      if (v.label.toLowerCase() == lower || v.name.toLowerCase() == lower) return v;
    }
    return Verdict.original;
  }
}

enum RiskLevel {
  low,
  medium,
  high;

  String get label {
    switch (this) {
      case RiskLevel.low:
        return 'Low';
      case RiskLevel.medium:
        return 'Medium';
      case RiskLevel.high:
        return 'High';
    }
  }
}

enum IndicatorType {
  frequency('Frequency inconsistencies'),
  texture('Texture anomalies'),
  metadata('Metadata mismatch'),
  diffusion('Diffusion artifacts'),
  compression('Compression artifacts'),
  lighting('Lighting inconsistencies');

  final String label;
  const IndicatorType(this.label);
}

enum ScoreCategory {
  texture('Texture'),
  metadata('Metadata'),
  lighting('Lighting'),
  frequency('Frequency'),
  noisePattern('Noise pattern'),
  compression('Compression'),
  edgeConsistency('Edge consistency'),
  colorDistribution('Color distribution');

  final String label;
  const ScoreCategory(this.label);
}

enum HeatmapMode {
  original('Original'),
  heatmap('Heatmap'),
  split('Split view');

  final String label;
  const HeatmapMode(this.label);
}
