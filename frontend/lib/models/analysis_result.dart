import 'dart:typed_data';

import 'analysis_components.dart';
import 'verdict.dart';

class AnalysisResult {
  final String id;
  final String? imagePath;
  final Uint8List? imageBytes;
  final String? fileName;
  final Verdict verdict;
  final double confidence; // 0..1
  final RiskLevel riskLevel;
  final String explanation;
  final Duration analysisDuration;
  final DateTime timestamp;
  final List<ForensicScore> scores;
  final List<DetectedIndicator> indicators;
  final HeatmapData? heatmap;
  final List<String> evidence;
  final Map<String, String> metadata;

  const AnalysisResult({
    required this.id,
    this.imagePath,
    this.imageBytes,
    this.fileName,
    required this.verdict,
    required this.confidence,
    required this.riskLevel,
    required this.explanation,
    required this.analysisDuration,
    required this.timestamp,
    required this.scores,
    required this.indicators,
    this.heatmap,
    required this.evidence,
    required this.metadata,
  });

  AnalysisResult copyWith({
    String? id,
    String? imagePath,
    Uint8List? imageBytes,
    String? fileName,
    Verdict? verdict,
    double? confidence,
    RiskLevel? riskLevel,
    String? explanation,
    Duration? analysisDuration,
    DateTime? timestamp,
    List<ForensicScore>? scores,
    List<DetectedIndicator>? indicators,
    HeatmapData? heatmap,
    List<String>? evidence,
    Map<String, String>? metadata,
  }) {
    return AnalysisResult(
      id: id ?? this.id,
      imagePath: imagePath ?? this.imagePath,
      imageBytes: imageBytes ?? this.imageBytes,
      fileName: fileName ?? this.fileName,
      verdict: verdict ?? this.verdict,
      confidence: confidence ?? this.confidence,
      riskLevel: riskLevel ?? this.riskLevel,
      explanation: explanation ?? this.explanation,
      analysisDuration: analysisDuration ?? this.analysisDuration,
      timestamp: timestamp ?? this.timestamp,
      scores: scores ?? this.scores,
      indicators: indicators ?? this.indicators,
      heatmap: heatmap ?? this.heatmap,
      evidence: evidence ?? this.evidence,
      metadata: metadata ?? this.metadata,
    );
  }
}
