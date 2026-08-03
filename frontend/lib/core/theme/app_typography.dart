import 'package:flutter/material.dart';

/// Global font family. Bundled with the app (see pubspec.yaml) so it works
/// on every platform without fetching anything from the network.
class AppFont {
  static const String family = 'Footlight MT Light';
}

class AppTypography {
  static TextStyle display(Color color) => TextStyle(
        fontFamily: AppFont.family,
        fontSize: 34,
        height: 1.1,
        fontWeight: FontWeight.w300,
        color: color,
      );

  static TextStyle headline(Color color) => TextStyle(
        fontFamily: AppFont.family,
        fontSize: 24,
        height: 1.2,
        fontWeight: FontWeight.w300,
        color: color,
      );

  static TextStyle title(Color color) => TextStyle(
        fontFamily: AppFont.family,
        fontSize: 18,
        height: 1.25,
        fontWeight: FontWeight.w300,
        color: color,
      );

  static TextStyle body(Color color) => TextStyle(
        fontFamily: AppFont.family,
        fontSize: 15,
        height: 1.45,
        fontWeight: FontWeight.w300,
        color: color,
      );

  static TextStyle label(Color color) => TextStyle(
        fontFamily: AppFont.family,
        fontSize: 13,
        height: 1.3,
        fontWeight: FontWeight.w400,
        color: color,
      );

  static TextStyle caption(Color color) => TextStyle(
        fontFamily: AppFont.family,
        fontSize: 11,
        height: 1.3,
        fontWeight: FontWeight.w400,
        letterSpacing: 0.3,
        color: color,
      );

  static TextStyle button(Color color) => TextStyle(
        fontFamily: AppFont.family,
        fontSize: 15,
        fontWeight: FontWeight.w400,
        letterSpacing: 0.2,
        color: color,
      );

  static TextStyle tab(Color color) => TextStyle(
        fontFamily: AppFont.family,
        fontSize: 13,
        fontWeight: FontWeight.w400,
        letterSpacing: 0.2,
        color: color,
      );
}
