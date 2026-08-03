import 'dart:math';
import 'dart:typed_data';

import '../../models/analysis_components.dart';
import '../../models/analysis_result.dart';
import '../../models/history_item.dart';
import '../../models/verdict.dart';

/// Deterministic, believable mock data for the whole app.
///
/// Seeded by integer seeds so the same input always produces the same result
/// (matching how a real backend keyed by content hash would behave).
class MockData {
  MockData._();

  static const List<String> fileNames = [
    'IMG_2041.jpg', 'IMG_2042.jpg', 'IMG_2055.jpg', 'IMG_2071.jpg',
    'IMG_2104.jpg', 'photo_031.png', 'photo_044.png', 'photo_052.png',
    'photo_063.png', 'photo_077.png', 'scan_014.jpg', 'scan_022.jpg',
    'scan_030.jpg', 'scan_041.jpg', 'scan_058.jpg', 'download_113.png',
    'download_124.png', 'download_136.png', 'download_141.png',
    'download_157.png', 'avatar_01.png', 'render_03.png', 'product_12.jpg',
    'event_07.jpg', 'profile_09.jpg',
  ];

  static const List<String> cameras = [
    'Apple iPhone 16 Pro', 'Samsung Galaxy S24 Ultra', 'Google Pixel 9',
    'Sony A7 IV', 'Canon EOS R5', 'Unknown', 'Adobe Firefly', 'Midjourney',
    'Stable Diffusion XL',
  ];

  static const List<String> software = [
    'Lightroom 7.4', 'Photoshop 25.3', 'Snapseed', 'None', 'None',
    'None', 'ComfyUI', 'Firefly 2', 'DALL-E 3',
  ];

  static const List<String> resolutions = [
    '4032 × 3024', '3072 × 4096', '2048 × 2048', '1024 × 1024',
    '1920 × 1080', '4080 × 3060', '1024 × 1536',
  ];

  static const List<String> evidencePool = [
    'Edge gradient analysis shows abrupt transitions near the subject boundary.',
    'JPEG quantization tables are inconsistent with the declared quality.',
    'Local noise statistics differ between adjacent regions of the image.',
    'Sensor noise pattern (PRNU) is absent across large areas.',
    'Facial landmark geometry sits outside the biometric expectation range.',
    'Color temperature shifts detected in the upper-left quadrant.',
    'Shadow direction is inconsistent with the scene light source.',
    'Metadata timestamp differs from the time implied by the content.',
    'Exif software field indicates an editing pipeline.',
    'Frequency-domain analysis reveals resampling lattice artifacts.',
  ];

  static const Map<IndicatorType, String> indicatorDescriptions = {
    IndicatorType.frequency: 'Periodic resampling artifacts visible in the frequency domain.',
    IndicatorType.texture: 'Texture detail degrades in specific regions while staying sharp elsewhere.',
    IndicatorType.metadata: 'Embedded metadata conflicts with the visible content.',
    IndicatorType.diffusion: 'Soft, watercolor-like artifacts consistent with diffusion synthesis.',
    IndicatorType.compression: 'Generation artefacts survive re-compression in isolated blocks.',
  };

  static Verdict _pickVerdict(Random rng) {
    final roll = rng.nextInt(100);
    if (roll < 28) return Verdict.original;
    if (roll < 68) return Verdict.aiEdited;
    return Verdict.aiGenerated;
  }

  static AnalysisResult buildAnalysisResult({
    required int seed,
    String? imagePath,
    Uint8List? imageBytes,
    String? fileName,
    DateTime? timestamp,
  }) {
    final rng = Random(seed);
    final verdict = _pickVerdict(rng);
    final name = fileName ?? fileNames[seed % fileNames.length];

    double confidence;
    RiskLevel riskLevel;
    switch (verdict) {
      case Verdict.original:
        confidence = 0.82 + rng.nextDouble() * 0.17;
        riskLevel = rng.nextInt(100) < 12 ? RiskLevel.medium : RiskLevel.low;
      case Verdict.aiEdited:
        confidence = 0.74 + rng.nextDouble() * 0.22;
        riskLevel = rng.nextInt(100) < 22 ? RiskLevel.high : RiskLevel.medium;
      case Verdict.aiGenerated:
        confidence = 0.86 + rng.nextDouble() * 0.13;
        riskLevel = rng.nextInt(100) < 18 ? RiskLevel.medium : RiskLevel.high;
    }

    final scores = List<ForensicScore>.generate(ScoreCategory.values.length, (i) {
      final category = ScoreCategory.values[i];
      final base = _baseScore(verdict, rng);
      return ForensicScore(
        category: category,
        value: (base + (rng.nextDouble() - 0.5) * 0.18).clamp(0.05, 0.99),
      );
    });

    final indicators = <DetectedIndicator>[];
    final indicatorCount = verdict == Verdict.original
        ? (rng.nextInt(100) < 30 ? 1 : 0)
        : verdict == Verdict.aiEdited
            ? 2 + rng.nextInt(3)
            : 3 + rng.nextInt(3);
    final shuffledTypes = List<IndicatorType>.of(IndicatorType.values)
      ..shuffle(rng);
    for (var i = 0; i < indicatorCount && i < shuffledTypes.length; i++) {
      final type = shuffledTypes[i];
      final strong = rng.nextBool();
      indicators.add(DetectedIndicator(
        type: type,
        confidence: 0.6 + rng.nextDouble() * 0.38,
        severity: strong ? 'Strong' : 'Moderate',
        description: indicatorDescriptions[type]!,
      ));
    }

    HeatmapData? heatmap;
    if (verdict != Verdict.original) {
      final regions = List<HeatmapRegion>.generate(1 + rng.nextInt(3), (i) {
        final w = 0.16 + rng.nextDouble() * 0.3;
        final h = 0.14 + rng.nextDouble() * 0.28;
        return HeatmapRegion(
          x: 0.08 + rng.nextDouble() * (0.9 - w),
          y: 0.08 + rng.nextDouble() * (0.9 - h),
          width: w,
          height: h,
          intensity: (0.45 + rng.nextDouble() * 0.5).clamp(0.0, 1.0),
          label: verdict == Verdict.aiGenerated
              ? 'Synthesized region'
              : 'Edited region',
        );
      });
      heatmap = HeatmapData(
        regions: regions,
        overallManipulation: verdict == Verdict.aiEdited
            ? 0.4 + rng.nextDouble() * 0.3
            : 0.7 + rng.nextDouble() * 0.25,
      );
    }

    final evidencePoolCopy = [...evidencePool]..shuffle(rng);
    final evidence = evidencePoolCopy.take(2 + rng.nextInt(2)).toList();
    if (verdict == Verdict.original) {
      evidence.insert(0, 'No anomalies above the confidence threshold were located.');
    }

    final explanation = StringBuffer(_explanationFor(verdict));
    if (indicators.isNotEmpty) {
      explanation
        ..write(' Strongest signal: ')
        ..write(indicators.first.description);
    } else {
      explanation.write(' Sensor and frequency analyses returned clean profiles.');
    }

    return AnalysisResult(
      id: 'ana_${seed.abs()}',
      imagePath: imagePath,
      imageBytes: imageBytes,
      fileName: name,
      verdict: verdict,
      confidence: confidence.clamp(0.0, 1.0),
      riskLevel: riskLevel,
      explanation: explanation.toString(),
      analysisDuration: Duration(
        milliseconds: 900 + (seed % 11) * 250 + rng.nextInt(400),
      ),
      timestamp: timestamp ?? DateTime.now(),
      scores: scores,
      indicators: indicators,
      heatmap: heatmap,
      evidence: evidence,
      metadata: {
        'Camera': cameras[seed % cameras.length],
        'Software': software[seed % software.length],
        'Resolution': resolutions[seed % resolutions.length],
        'Format': name.endsWith('.png') ? 'PNG' : 'JPEG',
        'File size': '${2 + (seed % 9)}.${rng.nextInt(9)} MB',
      },
    );
  }

  static double _baseScore(Verdict verdict, Random rng) {
    switch (verdict) {
      case Verdict.original:
        return 0.82 + rng.nextDouble() * 0.12;
      case Verdict.aiEdited:
        return 0.4 + rng.nextDouble() * 0.42;
      case Verdict.aiGenerated:
        return 0.18 + rng.nextDouble() * 0.4;
    }
  }

  static String _explanationFor(Verdict verdict) {
    switch (verdict) {
      case Verdict.original:
        return 'No significant manipulation detected. The image appears authentic.';
      case Verdict.aiEdited:
        return 'Evidence of AI-assisted editing detected. Parts of this image may have been altered.';
      case Verdict.aiGenerated:
        return 'Image appears to be fully or largely AI-generated.';
    }
  }

  /// Rebuilds a full report for a persisted history summary, keeping the
  /// stored verdict/confidence/risk consistent with the card the user tapped.
  static AnalysisResult fromHistoryItem(HistoryItem item) {
    final seed = item.id.hashCode.abs().clamp(1, 1 << 30);
    final result = buildAnalysisResult(
      seed: seed,
      fileName: item.fileName,
      timestamp: item.timestamp,
    );
    return result.copyWith(
      verdict: item.verdict,
      confidence: item.confidence,
      riskLevel: item.riskLevel,
    );
  }

  static List<HistoryItem> seedHistory(int count) {    final items = <HistoryItem>[];
    final now = DateTime.now();
    for (var i = 0; i < count; i++) {
      final seed = 2000 + i * 13;
      final rng = Random(seed);
      final result = buildAnalysisResult(
        seed: seed,
        fileName: fileNames[i % fileNames.length],
        timestamp: now.subtract(Duration(hours: i * 5 + rng.nextInt(4))),
      );
      items.add(HistoryItem(
        id: 'hist_$i',
        fileName: result.fileName,
        verdict: result.verdict,
        confidence: result.confidence,
        riskLevel: result.riskLevel,
        timestamp: result.timestamp,
        isFavorite: i % 8 == 0,
      ));
    }
    return items;
  }
}
