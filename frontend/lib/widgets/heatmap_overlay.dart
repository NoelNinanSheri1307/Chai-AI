import 'dart:math';

import 'package:flutter/material.dart';

import '../models/analysis_components.dart';
import '../models/verdict.dart';

/// Overlays heatmap regions onto a base image.
///
/// [mode] switches between showing the untouched image, the heatmap overlay,
/// and a side-by-side split view. [opacity] scales the overlay intensity.
class HeatmapOverlay extends StatelessWidget {
  final HeatmapData data;
  final Widget image;
  final HeatmapMode mode;
  final double opacity;

  const HeatmapOverlay({
    super.key,
    required this.data,
    required this.image,
    this.mode = HeatmapMode.heatmap,
    this.opacity = 0.8,
  });

  @override
  Widget build(BuildContext context) {
    if (mode == HeatmapMode.original || data.regions.isEmpty) {
      return image;
    }

    final overlay = IgnorePointer(
      child: CustomPaint(
        painter: _HeatmapPainter(data: data, opacity: opacity),
        child: const SizedBox.expand(),
      ),
    );

    if (mode == HeatmapMode.split) {
      return Stack(
        fit: StackFit.expand,
        children: [
          image,
          ClipRect(
            child: Align(
              alignment: Alignment.centerRight,
              child: FractionallySizedBox(
                widthFactor: 0.5,
                child: overlay,
              ),
            ),
          ),
        ],
      );
    }

    return Stack(
      fit: StackFit.expand,
      children: [image, overlay],
    );
  }
}

class _HeatmapPainter extends CustomPainter {
  final HeatmapData data;
  final double opacity;

  _HeatmapPainter({required this.data, required this.opacity});

  @override
  void paint(Canvas canvas, Size size) {
    if (size.isEmpty) return;

    final softTint = Paint()
      ..shader = LinearGradient(
        begin: Alignment.topCenter,
        end: Alignment.bottomCenter,
        colors: [
          const Color(0xFFFFB74D).withValues(alpha: 0.10 * opacity),
          Colors.transparent,
        ],
      ).createShader(Offset.zero & size);
    canvas.drawRect(Offset.zero & size, softTint);

    for (final region in data.regions) {
      final rect = Rect.fromLTWH(
        region.x * size.width,
        region.y * size.height,
        region.width * size.width,
        region.height * size.height,
      );
      final center = rect.center;
      final radius = max(rect.width, rect.height) * 0.9;
      final intensity = (opacity * region.intensity).clamp(0.0, 1.0);

      final paint = Paint()
        ..shader = RadialGradient(
          colors: [
            const Color(0xFFFF5252).withValues(alpha: 0.9 * intensity),
            const Color(0xFFFFB74D).withValues(alpha: 0.6 * intensity),
            const Color(0xFFFFE082).withValues(alpha: 0.3 * intensity),
            Colors.transparent,
          ],
          stops: const [0.0, 0.35, 0.65, 1.0],
        ).createShader(Rect.fromCircle(center: center, radius: radius));
      canvas.drawCircle(center, radius, paint);

      canvas.drawCircle(
        center,
        2,
        Paint()..color = const Color(0xFFFF5252).withValues(alpha: intensity),
      );
    }
  }

  @override
  bool shouldRepaint(covariant _HeatmapPainter oldDelegate) =>
      oldDelegate.data != data || oldDelegate.opacity != opacity;
}
