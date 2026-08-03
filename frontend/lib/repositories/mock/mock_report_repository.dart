import 'dart:typed_data';

import '../../models/analysis_result.dart';
import '../../services/pdf_report_builder.dart';
import '../../services/share_builder.dart';
import '../report_repository.dart';

class MockReportRepository implements ReportRepository {
  @override
  Future<Uint8List> generatePdf(AnalysisResult result) async {
    return PdfReportBuilder.build(result);
  }

  @override
  Future<String> generateShareText(AnalysisResult result) async {
    return ShareBuilder.buildText(result);
  }
}
