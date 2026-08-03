import 'dart:io';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;
import 'package:printing/printing.dart';
import '../models/analysis_result_model.dart';

class ReportService {
  static Future<void> generateReport(AnalysisResult result) async {
    final pdf = pw.Document();

    pdf.addPage(
      pw.Page(
        build: (context) {
          return pw.Column(
            crossAxisAlignment: pw.CrossAxisAlignment.start,
            children: [
              pw.Text(
                "Digital Authenticity Report",
                style: pw.TextStyle(
                  fontSize: 24,
                  fontWeight: pw.FontWeight.bold,
                ),
              ),
              pw.SizedBox(height: 20),
              pw.Text("Authenticity Score: ${result.authenticityScore}%"),
              pw.Text("Risk Level: ${result.riskLevel}"),
              pw.Text("Enforcement Action: ${result.enforcementAction}"),
              pw.SizedBox(height: 20),
              pw.Text("AI Score: ${(result.aiScore * 100).toInt()}%"),
              pw.Text(
                "Manipulation Score: ${(result.manipulationScore * 100).toInt()}%",
              ),
              pw.Text(
                "Frequency Score: ${(result.frequencyScore * 100).toInt()}%",
              ),
              pw.SizedBox(height: 20),
              pw.Text("Explanation:"),
              pw.Text(result.explanation),
            ],
          );
        },
      ),
    );

    await Printing.layoutPdf(onLayout: (format) async => pdf.save());
  }
}
