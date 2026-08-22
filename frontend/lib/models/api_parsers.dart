/// Parsers that convert the backend's `AnalysisResultDTO`, `HistoryItemDTO`
/// and `CompareResultDTO` JSON payloads into the frontend model objects.
///
/// The backend serializes camelCase shapes that match the frontend models, so
/// parsing is a thin, defensive mapping (numbers may arrive as int/double).
library;

import 'analysis_components.dart';
import 'analysis_result.dart';
import 'compare_result.dart';
import 'history_item.dart';
import 'verdict.dart';

Duration parseIso8601Duration(String value) {
  final match = RegExp(
    r'^PT(?:(\d+(?:\.\d+)?)H)?(?:(\d+(?:\.\d+)?)M)?(?:(\d+(?:\.\d+)?)S)?$',
  ).firstMatch(value.trim());
  if (match == null) return Duration.zero;
  final hours = double.tryParse(match.group(1) ?? '') ?? 0;
  final minutes = double.tryParse(match.group(2) ?? '') ?? 0;
  final seconds = double.tryParse(match.group(3) ?? '') ?? 0;
  return Duration(
    hours: hours.floor(),
    minutes: minutes.floor(),
    milliseconds: ((seconds * 1000).round()),
  );
}

T _enumByName<T extends Enum>(List<T> values, String name) {
  for (final value in values) {
    if (value.name.toLowerCase() == name.toLowerCase()) return value;
  }
  if (T == Verdict) {
    return Verdict.fromLabel(name) as T;
  }
  return values.first;
}

double _asDouble(dynamic value) => (value as num).toDouble();

ForensicScore _parseScore(Map<String, dynamic> json) => ForensicScore(
      category: _enumByName(ScoreCategory.values, json['category'] as String),
      value: _asDouble(json['value']),
    );

DetectedIndicator _parseIndicator(Map<String, dynamic> json) => DetectedIndicator(
      type: _enumByName(IndicatorType.values, json['type'] as String),
      confidence: _asDouble(json['confidence']),
      severity: json['severity'] as String,
      description: json['description'] as String,
    );

HeatmapRegion _parseRegion(Map<String, dynamic> json) => HeatmapRegion(
      x: _asDouble(json['x']),
      y: _asDouble(json['y']),
      width: _asDouble(json['width']),
      height: _asDouble(json['height']),
      intensity: _asDouble(json['intensity']),
      label: json['label'] as String,
    );

HeatmapData? _parseHeatmap(Map<String, dynamic>? json) {
  if (json == null) return null;
  final regions = (json['regions'] as List<dynamic>? ?? [])
      .map((e) => _parseRegion(e as Map<String, dynamic>))
      .toList();
  return HeatmapData(
    regions: regions,
    overallManipulation: _asDouble(json['overallManipulation']),
  );
}

AnalysisResult parseAnalysisResult(Map<String, dynamic> json) => AnalysisResult(
      id: json['id'] as String,
      imagePath: json['imagePath'] as String?,
      fileName: json['fileName'] as String?,
      verdict: _enumByName(Verdict.values, json['verdict'] as String),
      confidence: _asDouble(json['confidence']),
      riskLevel: _enumByName(RiskLevel.values, json['riskLevel'] as String),
      explanation: json['explanation'] as String,
      analysisDuration: parseIso8601Duration(json['analysisDuration'] as String),
      timestamp: DateTime.parse(json['timestamp'] as String),
      scores: (json['scores'] as List<dynamic>? ?? [])
          .map((e) => _parseScore(e as Map<String, dynamic>))
          .toList(),
      indicators: (json['indicators'] as List<dynamic>? ?? [])
          .map((e) => _parseIndicator(e as Map<String, dynamic>))
          .toList(),
      heatmap: _parseHeatmap(json['heatmap'] as Map<String, dynamic>?),
      evidence: (json['evidence'] as List<dynamic>? ?? [])
          .map((e) => e as String)
          .toList(),
      metadata:
          (json['metadata'] as Map<String, dynamic>? ?? {})
              .map((key, value) => MapEntry(key, value as String)),
    );

HistoryItem parseHistoryItem(Map<String, dynamic> json) => HistoryItem(
      id: json['id'] as String,
      imagePath: json['imagePath'] as String?,
      fileName: json['fileName'] as String?,
      verdict: _enumByName(Verdict.values, json['verdict'] as String),
      confidence: _asDouble(json['confidence']),
      riskLevel: _enumByName(RiskLevel.values, json['riskLevel'] as String),
      timestamp: DateTime.parse(json['timestamp'] as String),
      isFavorite: json['isFavorite'] as bool? ?? false,
    );

CompareResult parseCompareResult(Map<String, dynamic> json) => CompareResult(
      labelA: json['labelA'] as String,
      labelB: json['labelB'] as String,
      similarity: _asDouble(json['similarity']),
      aiProbability: _asDouble(json['aiProbability']),
      similarities: (json['similarities'] as List<dynamic>? ?? [])
          .map((e) => e as String)
          .toList(),
      differences: (json['differences'] as List<dynamic>? ?? [])
          .map((e) => e as String)
          .toList(),
      manipulatedRegions: (json['manipulatedRegions'] as List<dynamic>? ?? [])
          .map((e) => _parseRegion(e as Map<String, dynamic>))
          .toList(),
    );
