import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:yukta_authenticity_app/core/theme/app_theme.dart';
import 'package:yukta_authenticity_app/features/history/history_controller.dart';
import 'package:yukta_authenticity_app/features/result/result_screen.dart';
import 'package:yukta_authenticity_app/models/analysis_components.dart';
import 'package:yukta_authenticity_app/models/analysis_result.dart';
import 'package:yukta_authenticity_app/models/api_parsers.dart';
import 'package:yukta_authenticity_app/models/verdict.dart';
import 'package:yukta_authenticity_app/navigation/app_routes.dart';
import 'package:yukta_authenticity_app/repositories/mock/mock_history_repository.dart';
import 'package:yukta_authenticity_app/repositories/mock/mock_report_repository.dart';
import 'package:yukta_authenticity_app/repositories/report_repository.dart';
import 'package:yukta_authenticity_app/services/pdf_report_builder.dart';
import 'package:yukta_authenticity_app/services/share_service.dart';

void main() {
  test('DecisionProvenance parses correctly from json', () {
    final json = {
      'id': 'test-123',
      'fileName': 'sample.png',
      'verdict': 'AI_GENERATED',
      'confidence': 0.95,
      'riskLevel': 'HIGH',
      'explanation': 'Multi-source classification detected AI generation.',
      'analysisDuration': 'PT0.85S',
      'timestamp': '2026-08-23T12:00:00.000Z',
      'scores': [
        {'category': 'frequency', 'value': 0.88},
        {'category': 'lighting', 'value': 0.42},
      ],
      'indicators': [
        {
          'type': 'frequency',
          'confidence': 0.9,
          'severity': 'Strong',
          'description': 'High frequency grid patterns',
        }
      ],
      'evidence': ['Lattice artifacts in FFT spectrum.'],
      'metadata': {'Format': 'PNG', 'Resolution': '1024x1024'},
      'provenance': {
        'finalClassification': 'AI_GENERATED',
        'finalConfidence': 0.95,
        'chaiClassification': 'AI_GENERATED',
        'chaiConfidence': 0.88,
        'chaiAiProbability': 0.85,
        'chaiEditScore': 0.12,
        'sightengineStatus': 'success',
        'sightengineAiProbability': 0.98,
        'fusionWeightChai': 0.3,
        'fusionWeightSightengine': 0.7,
        'finalFusedProbability': 0.941,
        'decisionReason': 'Fused Sightengine 70% + Chai 30%',
        'evidence': ['Evidence line 1'],
      },
    };

    final result = parseAnalysisResult(json);
    expect(result.verdict, Verdict.aiGenerated);
    expect(result.confidence, 0.95);
    expect(result.provenance, isNotNull);
    expect(result.provenance!.isSightengineAvailable, isTrue);
    expect(result.provenance!.finalFusedProbability, 0.941);
    expect(result.provenance!.sightengineAiProbability, 0.98);
  });

  testWidgets('ResultScreen renders Authenticity Detection and Image Insights',
      (tester) async {
    final result = AnalysisResult(
      id: 'res-1',
      fileName: 'test.jpg',
      verdict: Verdict.aiGenerated,
      confidence: 0.92,
      riskLevel: RiskLevel.high,
      explanation: 'Image appears to be fully AI generated.',
      analysisDuration: const Duration(seconds: 1),
      timestamp: DateTime.now(),
      scores: const [
        ForensicScore(category: ScoreCategory.frequency, value: 0.85),
      ],
      indicators: const [
        DetectedIndicator(
          type: IndicatorType.frequency,
          confidence: 0.9,
          severity: 'Strong',
          description: 'Periodic resampling artifacts in frequency domain.',
        ),
      ],
      evidence: const ['FFT peaks detected.'],
      metadata: const {'Format': 'JPEG', 'Resolution': '2048x2048'},
      provenance: const DecisionProvenance(
        finalClassification: Verdict.aiGenerated,
        finalConfidence: 0.92,
        chaiClassification: Verdict.aiGenerated,
        chaiConfidence: 0.85,
        chaiAiProbability: 0.85,
        chaiEditScore: 0.10,
        sightengineStatus: 'success',
        sightengineAiProbability: 0.95,
        fusionWeightChai: 0.30,
        fusionWeightSightengine: 0.70,
        finalFusedProbability: 0.92,
        decisionReason: 'Sightengine + Chai multi-source fusion.',
      ),
    );

    final historyRepo = MockHistoryRepository();
    final reportRepo = MockReportRepository();
    final shareService = ShareService();

    tester.view.devicePixelRatio = 1.0;
    tester.view.physicalSize = const Size(1200, 3000);
    addTearDown(() {
      tester.view.resetDevicePixelRatio();
      tester.view.resetPhysicalSize();
    });

    await tester.pumpWidget(
      MultiProvider(
        providers: [
          ChangeNotifierProvider(
              create: (_) => HistoryController(historyRepo)),
          Provider<ReportRepository>.value(value: reportRepo),
          Provider<ShareService>.value(value: shareService),
        ],
        child: MaterialApp(
          theme: AppTheme.dark(),
          home: ResultScreen(args: ResultArgs(result)),
        ),
      ),
    );

    await tester.pumpAndSettle();

    // Verify Primary Feature
    expect(find.text('Authenticity Detection'), findsOneWidget);
    expect(find.text('Detection Sources'), findsOneWidget);
    expect(find.text('Sightengine'), findsOneWidget);
    expect(find.text('Chai AI'), findsOneWidget);

    // Verify Secondary Feature
    expect(find.text('Image Insights'), findsOneWidget);
    expect(find.text('Image Information'), findsOneWidget);
    expect(find.text('Visual & Signal Analysis'), findsOneWidget);
  });



  testWidgets('ResultScreen shows fallback banner when Sightengine is offline',
      (tester) async {
    final result = AnalysisResult(
      id: 'res-2',
      fileName: 'fallback.jpg',
      verdict: Verdict.original,
      confidence: 0.84,
      riskLevel: RiskLevel.low,
      explanation: 'No manipulation detected.',
      analysisDuration: const Duration(seconds: 1),
      timestamp: DateTime.now(),
      scores: const [
        ForensicScore(category: ScoreCategory.lighting, value: 0.80),
      ],
      indicators: const [],
      evidence: const ['Consistent illumination.'],
      metadata: const {'Format': 'JPEG'},
      provenance: const DecisionProvenance(
        finalClassification: Verdict.original,
        finalConfidence: 0.84,
        chaiClassification: Verdict.original,
        chaiConfidence: 0.84,
        chaiAiProbability: 0.16,
        chaiEditScore: 0.05,
        sightengineStatus: 'unconfigured',
        fusionWeightChai: 1.0,
        fusionWeightSightengine: 0.0,
        finalFusedProbability: 0.16,
        decisionReason: 'External verification unavailable; Chai only.',
      ),
    );

    final historyRepo = MockHistoryRepository();
    final reportRepo = MockReportRepository();
    final shareService = ShareService();

    tester.view.devicePixelRatio = 1.0;
    tester.view.physicalSize = const Size(1200, 3000);
    addTearDown(() {
      tester.view.resetDevicePixelRatio();
      tester.view.resetPhysicalSize();
    });

    await tester.pumpWidget(
      MultiProvider(
        providers: [
          ChangeNotifierProvider(
              create: (_) => HistoryController(historyRepo)),
          Provider<ReportRepository>.value(value: reportRepo),
          Provider<ShareService>.value(value: shareService),
        ],
        child: MaterialApp(
          theme: AppTheme.dark(),
          home: ResultScreen(args: ResultArgs(result)),
        ),
      ),
    );


    await tester.pumpAndSettle();

    expect(
      find.text(
        'External verification unavailable. Classification based on Chai forensic analysis only.',
      ),
      findsOneWidget,
    );
  });

  test('PdfReportBuilder generates PDF with Authenticity & Insights structure',
      () async {
    final result = AnalysisResult(
      id: 'res-pdf',
      fileName: 'doc.jpg',
      verdict: Verdict.aiEdited,
      confidence: 0.88,
      riskLevel: RiskLevel.medium,
      explanation: 'Localized manipulation detected.',
      analysisDuration: const Duration(seconds: 1),
      timestamp: DateTime.now(),
      scores: const [
        ForensicScore(category: ScoreCategory.texture, value: 0.75),
      ],
      indicators: const [],
      evidence: const ['Inconsistent grain.'],
      metadata: const {'Format': 'JPEG'},
    );

    final pdfBytes = await PdfReportBuilder.build(result);
    expect(pdfBytes, isNotNull);
    expect(pdfBytes.isNotEmpty, isTrue);
  });
}
