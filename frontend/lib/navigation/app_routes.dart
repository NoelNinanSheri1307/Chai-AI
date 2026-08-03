import 'dart:typed_data';

import '../models/analysis_result.dart';

class AppRoutes {
  static const String splash = '/';
  static const String onboarding = '/onboarding';
  static const String home = '/home';
  static const String upload = '/upload';
  static const String processing = '/processing';
  static const String result = '/result';
  static const String heatmap = '/heatmap';
  static const String report = '/report';
  static const String history = '/history';
  static const String compare = '/compare';
  static const String settings = '/settings';
  static const String about = '/about';
}

class ProcessingArgs {
  final String name;
  final Uint8List? bytes;
  const ProcessingArgs(this.name, this.bytes);
}

class ResultArgs {
  final AnalysisResult result;
  const ResultArgs(this.result);
}

class HeatmapArgs {
  final AnalysisResult result;
  const HeatmapArgs(this.result);
}

class ReportArgs {
  final AnalysisResult result;
  const ReportArgs(this.result);
}
