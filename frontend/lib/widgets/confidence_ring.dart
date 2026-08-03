import 'dart:math';

import 'package:flutter/material.dart';

import '../core/theme/app_dimensions.dart';
import '../core/theme/app_typography.dart';
import '../core/utils/context_ext.dart';

/// Circular confidence gauge with an animated sweep.
class ConfidenceRing extends StatefulWidget {
  final double value; // 0..1
  final Color color;
  final double size;
  final String? centerLabel;

  const ConfidenceRing({
    super.key,
    required this.value,
    required this.color,
    this.size = 200,
    this.centerLabel,
  });

  @override
  State<ConfidenceRing> createState() => _ConfidenceRingState();
}

class _ConfidenceRingState extends State<ConfidenceRing>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late final CurvedAnimation _curved;
  late Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: AppDurations.slow,
    );
    _curved = CurvedAnimation(parent: _controller, curve: AppCurves.emphaSized);
    _animation = Tween(begin: 0.0, end: widget.value).animate(_curved);
    _controller.forward();
  }

  @override
  void didUpdateWidget(covariant ConfidenceRing oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.value != widget.value) {
      _animation = Tween(begin: 0.0, end: widget.value).animate(_curved);
      _controller.forward(from: 0);
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    _curved.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    return AnimatedBuilder(
      animation: _animation,
      builder: (context, child) {
        final progress = _animation.value;
        return CustomPaint(
          size: Size(widget.size, widget.size),
          painter: _RingPainter(
            progress: progress,
            color: widget.color,
            trackColor: colors.surfaceMuted,
            strokeWidth: widget.size * 0.055,
          ),
          child: Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  '${(progress * 100).round()}%',
                  style: AppTypography.display(colors.textPrimary),
                ),
                if (widget.centerLabel != null)
                  Text(
                    widget.centerLabel!,
                    style: AppTypography.caption(colors.textTertiary),
                  ),
              ],
            ),
          ),
        );
      },
    );
  }
}

class _RingPainter extends CustomPainter {
  final double progress;
  final Color color;
  final Color trackColor;
  final double strokeWidth;

  _RingPainter({
    required this.progress,
    required this.color,
    required this.trackColor,
    required this.strokeWidth,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final center = size.center(Offset.zero);
    final radius = (min(size.width, size.height) - strokeWidth) / 2;
    final rect = Rect.fromCircle(center: center, radius: radius);

    final track = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = strokeWidth
      ..color = trackColor;
    canvas.drawCircle(center, radius, track);

    final sweep = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = strokeWidth
      ..strokeCap = StrokeCap.round
      ..color = color;
    canvas.drawArc(
      rect,
      -pi / 2,
      2 * pi * progress,
      false,
      sweep,
    );
  }

  @override
  bool shouldRepaint(covariant _RingPainter oldDelegate) =>
      oldDelegate.progress != progress ||
      oldDelegate.color != color ||
      oldDelegate.trackColor != trackColor;
}
