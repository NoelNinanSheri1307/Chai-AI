import 'dart:typed_data';

import '../models/analysis_result.dart';

/// Contract for report rendering.
///
/// The mock implementation renders PDFs locally. An [ApiReportRepository]
/// backed by the future backend would fetch the rendered report bytes from the
/// server while keeping the same interface.
abstract class ReportRepository {
  Future<Uint8List> generatePdf(AnalysisResult result);

  Future<String> generateShareText(AnalysisResult result);
}
