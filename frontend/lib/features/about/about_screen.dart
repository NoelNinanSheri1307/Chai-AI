import 'package:flutter/material.dart';

import '../../core/theme/app_dimensions.dart';
import '../../core/theme/app_typography.dart';
import '../../core/utils/context_ext.dart';
import '../../widgets/app_card.dart';

class AboutScreen extends StatelessWidget {
  const AboutScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    return Scaffold(
      appBar: AppBar(title: const Text('About')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(AppSpacing.lg),
          children: [
            const SizedBox(height: AppSpacing.lg),
            Center(
              child: ClipRRect(
                borderRadius: BorderRadius.circular(AppRadius.xl),
                child: Image.asset(
                  'assets/ChaiAILogo.png',
                  width: 96,
                  height: 96,
                  fit: BoxFit.cover,
                ),
              ),
            ),
            const SizedBox(height: AppSpacing.lg),
            Center(
              child: Text(
                'Chai AI',
                style: AppTypography.headline(colors.textPrimary),
              ),
            ),
            const SizedBox(height: AppSpacing.sm),
            Center(
              child: Text(
                'Image Authenticity & Forensic Analysis',
                style: AppTypography.caption(colors.textTertiary),
              ),
            ),
            const SizedBox(height: AppSpacing.sm),
            Center(
              child: Text(
                'Version 1.0.0',
                style: AppTypography.caption(colors.textTertiary),
              ),
            ),
            const SizedBox(height: AppSpacing.xl),
            AppCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'What is Chai AI?',
                    style: AppTypography.title(colors.textPrimary),
                  ),
                  const SizedBox(height: AppSpacing.sm),
                  Text(
                    'Chai AI delivers image authenticity detection supported by '
                    'deep forensic image insights. It determines whether an image '
                    'is Real, AI-Generated, or AI-Edited using multi-source verification '
                    'and extracts supporting forensic signals across spatial frequency, '
                    'lighting, texture, noise, compression, and visual heatmaps.',
                    style: AppTypography.body(colors.textSecondary),
                  ),

                ],
              ),
            ),
            const SizedBox(height: AppSpacing.lg),
            AppCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Data & Processing',
                    style: AppTypography.title(colors.textPrimary),
                  ),
                  const SizedBox(height: AppSpacing.sm),
                  Text(
                    'The current build runs on a local mock repository so the '
                    'entire product can be explored without a server. Analysis '
                    'history is stored locally on your device. When the analysis '
                    'backend is available, images will be sent to the endpoint '
                    'configured in Settings.',
                    style: AppTypography.body(colors.textSecondary),
                  ),
                ],
              ),
            ),
            const SizedBox(height: AppSpacing.lg),
            Center(
              child: Text(
                'Built with Flutter',
                style: AppTypography.caption(colors.textTertiary),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
