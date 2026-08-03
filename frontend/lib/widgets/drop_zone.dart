import 'package:cross_file/cross_file.dart';
import 'package:desktop_drop/desktop_drop.dart';
import 'package:flutter/material.dart';

import '../core/theme/app_dimensions.dart';
import '../core/theme/app_typography.dart';
import '../core/utils/context_ext.dart';

/// Drag-and-drop target for desktop and web builds. Falls back gracefully on
/// platforms where dropping is unsupported (mobile).
class DragDropZone extends StatefulWidget {
  final void Function(List<XFile> files) onFiles;
  final Widget child;

  const DragDropZone({super.key, required this.onFiles, required this.child});

  @override
  State<DragDropZone> createState() => _DragDropZoneState();
}

class _DragDropZoneState extends State<DragDropZone> {
  bool _active = false;

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    return DropTarget(
      onDragEntered: (_) => setState(() => _active = true),
      onDragExited: (_) => setState(() => _active = false),
      onDragDone: (details) {
        setState(() => _active = false);
        if (details.files.isNotEmpty) widget.onFiles(details.files);
      },
      child: AnimatedContainer(
        duration: AppDurations.fast,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(AppRadius.lg),
          border: Border.all(
            color: _active ? colors.accent : Colors.transparent,
            width: 1.6,
          ),
        ),
        child: widget.child,
      ),
    );
  }
}

/// Banner content for an empty drop target.
class DropHint extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;

  const DropHint({
    super.key,
    required this.icon,
    required this.title,
    required this.subtitle,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 56,
          height: 56,
          decoration: BoxDecoration(
            color: colors.accentSoft,
            borderRadius: BorderRadius.circular(AppRadius.xl),
          ),
          child: Icon(icon, size: 26, color: colors.accent),
        ),
        const SizedBox(height: AppSpacing.md),
        Text(title, style: AppTypography.title(colors.textPrimary)),
        const SizedBox(height: AppSpacing.xs),
        Text(
          subtitle,
          textAlign: TextAlign.center,
          style: AppTypography.caption(colors.textTertiary),
        ),
      ],
    );
  }
}
