import 'package:flutter/material.dart';

import '../core/theme/app_dimensions.dart';

/// Fade + slide entrance animation. Pass [delayMs] to stagger list items.
class FadeIn extends StatefulWidget {
  final Widget child;
  final Duration duration;
  final int delayMs;
  final double slideDistance;

  const FadeIn({
    super.key,
    required this.child,
    this.duration = AppDurations.base,
    this.delayMs = 0,
    this.slideDistance = 12,
  });

  @override
  State<FadeIn> createState() => _FadeInState();
}

class _FadeInState extends State<FadeIn>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late final Animation<double> _opacity;
  late final Animation<Offset> _slide;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: widget.duration,
    );
    final curve = CurvedAnimation(parent: _controller, curve: AppCurves.standard);
    _opacity = curve;
    _slide = Tween<Offset>(
      begin: Offset(0, widget.slideDistance / 200),
      end: Offset.zero,
    ).animate(curve);
    if (widget.delayMs > 0) {
      Future<void>.delayed(
        Duration(milliseconds: widget.delayMs),
        () {
          if (mounted) _controller.forward();
        },
      );
    } else {
      _controller.forward();
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) => FadeTransition(
        opacity: _opacity,
        child: SlideTransition(position: _slide, child: child),
      ),
      child: widget.child,
    );
  }
}
