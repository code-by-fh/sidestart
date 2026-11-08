import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sidestart/main.dart';

void main() {
  testWidgets('increment and reset work; reset starts disabled', (tester) async {
    await tester.pumpWidget(const SideStartApp());
    final counter = find.byKey(const ValueKey('counter-value'));
    final increment = find.byKey(const ValueKey('increment-button'));
    final reset = find.byKey(const ValueKey('reset-button'));

    expect(tester.widget<Text>(counter).data, '0');
    expect(tester.widget<TextButton>(reset).onPressed, isNull);

    await tester.tap(increment);
    await tester.pump();
    await tester.tap(increment);
    await tester.pump();
    expect(tester.widget<Text>(counter).data, '2');

    await tester.tap(reset);
    await tester.pump();
    expect(tester.widget<Text>(counter).data, '0');
    expect(tester.widget<TextButton>(reset).onPressed, isNull);
  });

  testWidgets('small screen and large text remain usable', (tester) async {
    tester.view.physicalSize = const Size(320, 568);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(
      MaterialApp(
        home: MediaQuery(
          data: const MediaQueryData(textScaler: TextScaler.linear(2)),
          child: const HomePage(),
        ),
      ),
    );
    final increment = find.byKey(const ValueKey('increment-button'));
    await tester.ensureVisible(increment);
    await tester.tap(increment);
    await tester.pump();
    expect(tester.takeException(), isNull);
    expect(
      tester.widget<Text>(find.byKey(const ValueKey('counter-value'))).data,
      '1',
    );
  });
}
