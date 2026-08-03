import 'verdict.dart';

class HistoryItem {
  final String id;
  final String? imagePath;
  final String? fileName;
  final Verdict verdict;
  final double confidence; // 0..1
  final RiskLevel riskLevel;
  final DateTime timestamp;
  final bool isFavorite;

  const HistoryItem({
    required this.id,
    this.imagePath,
    this.fileName,
    required this.verdict,
    required this.confidence,
    required this.riskLevel,
    required this.timestamp,
    this.isFavorite = false,
  });

  HistoryItem copyWith({
    String? id,
    String? imagePath,
    String? fileName,
    Verdict? verdict,
    double? confidence,
    RiskLevel? riskLevel,
    DateTime? timestamp,
    bool? isFavorite,
  }) {
    return HistoryItem(
      id: id ?? this.id,
      imagePath: imagePath ?? this.imagePath,
      fileName: fileName ?? this.fileName,
      verdict: verdict ?? this.verdict,
      confidence: confidence ?? this.confidence,
      riskLevel: riskLevel ?? this.riskLevel,
      timestamp: timestamp ?? this.timestamp,
      isFavorite: isFavorite ?? this.isFavorite,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'imagePath': imagePath,
        'fileName': fileName,
        'verdict': verdict.name,
        'confidence': confidence,
        'riskLevel': riskLevel.name,
        'timestamp': timestamp.toIso8601String(),
        'isFavorite': isFavorite,
      };

  factory HistoryItem.fromJson(Map<String, dynamic> json) => HistoryItem(
        id: json['id'] as String,
        imagePath: json['imagePath'] as String?,
        fileName: json['fileName'] as String?,
        verdict: Verdict.values.byName(json['verdict'] as String),
        confidence: (json['confidence'] as num).toDouble(),
        riskLevel: RiskLevel.values.byName(json['riskLevel'] as String),
        timestamp: DateTime.parse(json['timestamp'] as String),
        isFavorite: json['isFavorite'] as bool? ?? false,
      );
}
