import '../models/analysis_result.dart';

class ShareBuilder {
  static String buildText(AnalysisResult result) {
    final buffer = StringBuffer()
      ..writeln('Chai AI — Authenticity Analysis')
      ..writeln()
      ..writeln('File: ${result.fileName ?? 'Image'}')
      ..writeln('Verdict: ${result.verdict.label}')
      ..writeln(
        'Confidence: ${(result.confidence * 100).round()}% · Risk: ${result.riskLevel.label}',
      )
      ..writeln('Time: ${_timeLabel(result)}')
      ..writeln()
      ..write(result.explanation);
    return buffer.toString();
  }

  static String _timeLabel(AnalysisResult result) {
    final dt = result.timestamp.toLocal();
    String two(int n) => n.toString().padLeft(2, '0');
    return '${two(dt.hour)}:${two(dt.minute)}';
  }
}
