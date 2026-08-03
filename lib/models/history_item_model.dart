import 'dart:convert';

class HistoryItem {
  final String id;
  final String? imagePath;
  final double authenticityScore;
  final String riskLevel;
  final DateTime timestamp;
  final String type; // "analysis" or "safety"

  HistoryItem({
    required this.id,
    required this.imagePath,
    required this.authenticityScore,
    required this.riskLevel,
    required this.timestamp,
    required this.type,
  });

  Map<String, dynamic> toMap() {
    return {
      "id": id,
      "imagePath": imagePath,
      "authenticityScore": authenticityScore,
      "riskLevel": riskLevel,
      "timestamp": timestamp.toIso8601String(),
      "type": type,
    };
  }

  factory HistoryItem.fromMap(Map<String, dynamic> map) {
    return HistoryItem(
      id: map["id"],
      imagePath: map["imagePath"],
      authenticityScore: (map["authenticityScore"] as num).toDouble(),
      riskLevel: map["riskLevel"],
      timestamp: DateTime.parse(map["timestamp"]),
      type: map["type"],
    );
  }

  String toJson() => json.encode(toMap());

  factory HistoryItem.fromJson(String source) =>
      HistoryItem.fromMap(json.decode(source));
}
