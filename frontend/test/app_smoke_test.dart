import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:yukta_authenticity_app/main.dart';

void main() {
  testWidgets('app boots to splash then onboarding on first launch',
      (tester) async {
    SharedPreferences.setMockInitialValues({});

    await tester.pumpWidget(const ChaiApp());
    await tester.pump(const Duration(milliseconds: 200));

    expect(find.text('Chai AI'), findsOneWidget);

    await tester.pump(const Duration(seconds: 3));
    await tester.pumpAndSettle();

    expect(find.text('Authenticity, verified'), findsOneWidget);
  });

  testWidgets('app skips onboarding when already seen', (tester) async {
    SharedPreferences.setMockInitialValues({
      'chai_onboarding_seen': true,
    });

    await tester.pumpWidget(const ChaiApp());
    await tester.pump(const Duration(seconds: 3));
    await tester.pumpAndSettle();

    expect(find.text('Analyze an image'), findsOneWidget);
  });
}
