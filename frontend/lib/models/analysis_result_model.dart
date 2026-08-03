// lib/models/analysis_result_model.dart

class AnalysisResult {
  final double authenticityScore;
  final String riskLevel;
  final String enforcementAction;

  final double aiScore;
  final double manipulationScore;
  final double frequencyScore;

  final bool metadataFlag;
  final String explanation;

  AnalysisResult({
    required this.authenticityScore,
    required this.riskLevel,
    required this.enforcementAction,
    required this.aiScore,
    required this.manipulationScore,
    required this.frequencyScore,
    required this.metadataFlag,
    required this.explanation,
  });
}
