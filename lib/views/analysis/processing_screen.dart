import 'dart:async';
import 'dart:io';
import 'package:flutter/material.dart';
import '../../core/spacing.dart';
import '../../core/app_colors.dart';
import '../../core/app_text_styles.dart';
import '../../services/analysis_screen.dart';
import '../../models/analysis_result_model.dart';
import '../result/result_screen.dart';

class ProcessingScreen extends StatefulWidget {
  final String imagePath;

  const ProcessingScreen({super.key, required this.imagePath});

  @override
  State<ProcessingScreen> createState() => _ProcessingScreenState();
}

class _ProcessingScreenState extends State<ProcessingScreen> {
  int _currentStep = 0;
  bool _completed = false;

  final List<String> _steps = [
    "Running AI Detection Layer",
    "Performing Frequency Analysis",
    "Executing ELA Forensics",
    "Scanning Metadata Integrity",
    "Fusion & Risk Scoring",
    "Generating Final Verdict",
  ];

  @override
  void initState() {
    super.initState();
    _runAnalysis();
    _animateSteps();
  }

  // Backend Call (UNCHANGED)
  void _runAnalysis() async {
    try {
      final AnalysisResult result = await AnalysisService.analyzeImage(
        File(widget.imagePath),
      );

      if (!mounted) return;

      setState(() {
        _completed = true;
      });

      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (_) =>
              ResultScreen(result: result, imagePath: widget.imagePath),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text("Analysis failed")));
      Navigator.pop(context);
    }
  }

  // UI Animation Loop
  void _animateSteps() async {
    while (!_completed) {
      for (int i = 0; i < _steps.length; i++) {
        if (_completed) return;
        await Future.delayed(const Duration(milliseconds: 1400));
        if (!mounted) return;
        setState(() {
          _currentStep = i;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    final primaryText = isDark
        ? AppColors.darkTextPrimary
        : AppColors.lightTextPrimary;
    final secondaryText = isDark
        ? AppColors.darkTextSecondary
        : AppColors.lightTextSecondary;

    return Scaffold(
      appBar: AppBar(
        title: const Text("Processing"),
        automaticallyImplyLeading: false,
      ),
      body: Padding(
        padding: const EdgeInsets.all(AppSpacing.lg),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              "Analyzing Image",
              style: AppTextStyles.headingLarge(primaryText),
            ),
            const SizedBox(height: AppSpacing.sm),
            Text(
              "AI Forensic Engine is evaluating authenticity",
              style: AppTextStyles.body(secondaryText),
            ),
            const SizedBox(height: AppSpacing.xl),

            Expanded(
              child: ListView.builder(
                itemCount: _steps.length,
                itemBuilder: (context, index) {
                  final isActive = index <= _currentStep;

                  return AnimatedOpacity(
                    duration: const Duration(milliseconds: 600),
                    opacity: isActive ? 1.0 : 0.3,
                    child: AnimatedSlide(
                      duration: const Duration(milliseconds: 600),
                      offset: isActive ? Offset.zero : const Offset(0.2, 0),
                      curve: Curves.easeOut,
                      child: Padding(
                        padding: const EdgeInsets.only(bottom: AppSpacing.md),
                        child: Row(
                          children: [
                            AnimatedSwitcher(
                              duration: const Duration(milliseconds: 400),
                              child: Icon(
                                isActive
                                    ? Icons.check_circle
                                    : Icons.radio_button_unchecked,
                                key: ValueKey(isActive),
                                color: isActive
                                    ? AppColors.accentBlue
                                    : secondaryText,
                              ),
                            ),
                            const SizedBox(width: AppSpacing.md),
                            Expanded(
                              child: Text(
                                _steps[index],
                                style: AppTextStyles.body(
                                  isActive ? primaryText : secondaryText,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  );
                },
              ),
            ),

            const SizedBox(height: 12),
            LinearProgressIndicator(
              minHeight: 6,
              borderRadius: BorderRadius.circular(10),
            ),
          ],
        ),
      ),
    );
  }
}
