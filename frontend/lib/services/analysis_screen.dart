import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import '../models/analysis_result_model.dart';

class AnalysisService {
  static const String baseUrl = "http://localhost:8000";

  static Future<AnalysisResult> analyzeImage(File imageFile) async {
    final uri = Uri.parse("$baseUrl/analyze");

    final request = http.MultipartRequest("POST", uri);

    request.files.add(
      await http.MultipartFile.fromPath(
        "file",
        imageFile.path,
      ),
    );

    final response = await request.send();
    final responseBody = await response.stream.bytesToString();

    if (response.statusCode != 200) {
      throw Exception("Server error: ${response.statusCode}");
    }

    final decoded = json.decode(responseBody);

    if (decoded["status"] != "success") {
      throw Exception("Analysis failed");
    }

    final data = decoded["data"];
    final typeBlock = data["type"] ?? {};

    final double aiScore =
        (typeBlock["ai_generated"] ?? 0).toDouble();

    final double manipulationScore =
        (typeBlock["manipulation_score"] ?? 0).toDouble();

    final String finalResult =
        data["Final Result"] ?? "Unknown";

    final String summary =
        data["forensic_summary"] ?? "";

    String riskLevel;
    String enforcementAction;

    if (finalResult == "Real") {
      riskLevel = "Low";
      enforcementAction = "Allow";
    } else if (finalResult == "AI Edited") {
      riskLevel = "Medium";
      enforcementAction = "Review";
    } else {
      riskLevel = "High";
      enforcementAction = "Block";
    }

    // FIXED: Explicit double conversion
    final double authenticity =
        ((1 - aiScore) * 100).clamp(0.0, 100.0).toDouble();

    return AnalysisResult(
      authenticityScore: authenticity,
      riskLevel: riskLevel,
      enforcementAction: enforcementAction,
      aiScore: aiScore,
      manipulationScore: manipulationScore,
      frequencyScore: 0.0,
      metadataFlag: false,
      explanation: summary,
    );
  }
}
