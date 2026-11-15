import assert from "node:assert/strict";
import test from "node:test";

import {
  addDrawSvgTransition,
  addExplicitStateTransition,
  addCountUp,
  addEvidenceHold,
  addFlowPath,
  addKeywordEmphasis,
  addMaskedTextCascade,
  addMapPanAndPin,
  addModelCompareCard,
  addMorphSvgTransition,
  addMotionPathFollower,
  addPhysics2DTransition,
  addPhysicsPropsTransition,
  addSelectionRail,
  addTextReplacementTransition,
  addTactileLanding,
  createCustomBounceProfile,
  createCustomEaseProfile,
  createCustomWiggleProfile,
  createTextPluginConfig,
  mapRange,
  normalizeRange,
  precomputeDistributedValues,
  snapValue
} from "./editorial-motion.js";

const fakeTimeline = () => {
  const calls = [];
  const timeline = { calls };
  for (const method of ["set", "to", "fromTo"]) {
    timeline[method] = (...args) => {
      calls.push([method, ...args]);
      return timeline;
    };
  }
  return timeline;
};

test("keyword emphasis schedules color before marker completion", () => {
  const timeline = fakeTimeline();
  const end = addKeywordEmphasis(timeline, {
    target: {},
    marker: {},
    start: 1
  });

  assert.deepEqual(timeline.calls.map(([method]) => method), ["to", "fromTo"]);
  assert.equal(timeline.calls[0][3], 1);
  assert.equal(timeline.calls[1][4], 1.08);
  assert.equal(end, 1.4);
});

test("count up remains controlled by supplied timeline", () => {
  const timeline = fakeTimeline();
  const target = { textContent: "" };
  const end = addCountUp(timeline, { target, to: 12, duration: 0.5 });

  assert.deepEqual(timeline.calls.map(([method]) => method), ["set", "fromTo"]);
  assert.equal(timeline.calls[0][2].textContent, "0");
  assert.equal(timeline.calls[1][3].value, 12);
  assert.equal(end, 0.5);
});

test("flow path derives SVG length and delays nodes", () => {
  const timeline = fakeTimeline();
  const path = { getTotalLength: () => 240 };
  const end = addFlowPath(timeline, { path, nodes: [{}, {}], duration: 1 });

  assert.equal(timeline.calls[0][2].strokeDasharray, 240);
  assert.equal(timeline.calls[1][2].strokeDashoffset, 0);
  assert.equal(timeline.calls[2][3], 0.35);
  assert.equal(end, 1);
});

test("masked text cascade uses explicit endpoints and deterministic stagger", () => {
  const timeline = fakeTimeline();
  const end = addMaskedTextCascade(timeline, {
    targets: [{}, {}, {}],
    start: 1,
    duration: 0.4,
    stagger: { each: 0.1, from: "center" }
  });

  assert.equal(timeline.calls[0][0], "fromTo");
  assert.deepEqual(timeline.calls[0][2], { y: 28, autoAlpha: 0, rotation: 0 });
  assert.equal(timeline.calls[0][3].immediateRender, true);
  assert.equal(timeline.calls[0][4], 1);
  assert.ok(Math.abs(end - 1.6) < Number.EPSILON * 4);
});

test("masked text cascade rejects random stagger", () => {
  assert.throws(() => addMaskedTextCascade(fakeTimeline(), {
    targets: [{}],
    stagger: { each: 0.1, from: "random" }
  }), /random stagger is not seek-safe/);
});

test("selection rail schedules item and panel handoff on one timeline", () => {
  const timeline = fakeTimeline();
  const end = addSelectionRail(timeline, {
    previousItem: {},
    nextItem: {},
    previousPanel: {},
    nextPanel: {},
    start: 2
  });

  assert.deepEqual(timeline.calls.map(([method]) => method), ["to", "fromTo", "to", "fromTo"]);
  assert.equal(timeline.calls[3][4], 2.1);
  assert.equal(end, 2.48);
});

test("selection rail can align item promotion with a fast panel handoff", () => {
  const timeline = fakeTimeline();
  const end = addSelectionRail(timeline, {
    previousItem: {},
    nextItem: {},
    previousPanel: {},
    nextPanel: {},
    start: 2,
    itemDuration: 0.24,
    itemOffset: 0.14,
    panelDuration: 0.26,
    panelExitDuration: 0.18,
    panelOffset: 0.12
  });

  assert.equal(timeline.calls[0][3], 2.14);
  assert.equal(timeline.calls[1][4], 2.14);
  assert.equal(timeline.calls[2][2].duration, 0.18);
  assert.equal(timeline.calls[3][4], 2.12);
  assert.equal(end, 2.38);
});

test("explicit state transition rejects layout properties", () => {
  assert.throws(() => addExplicitStateTransition(fakeTimeline(), {
    target: {},
    from: { left: 20, scale: 0.8 },
    to: { left: 0, scale: 1 }
  }), /cannot animate left/);
});

test("explicit state transition schedules caller-supplied transform states", () => {
  const timeline = fakeTimeline();
  const end = addExplicitStateTransition(timeline, {
    target: {},
    from: { x: -120, y: 20, scale: 0.8, rotation: -4 },
    to: { x: 0, y: 0, scale: 1, rotation: 0 },
    start: 0.5,
    duration: 0.7
  });

  assert.equal(timeline.calls[0][0], "fromTo");
  assert.equal(timeline.calls[0][3].immediateRender, false);
  assert.equal(end, 1.2);
});

test("motion path follower requires explicit path and alignment", () => {
  assert.throws(() => addMotionPathFollower(fakeTimeline(), {
    target: {},
    path: "#route"
  }), /missing align/);
});

test("motion path follower emits plugin config without owning registration", () => {
  const timeline = fakeTimeline();
  const end = addMotionPathFollower(timeline, {
    target: {},
    path: "#route",
    align: "#route",
    autoRotate: true,
    start: 1.2,
    duration: 0.8
  });

  assert.equal(timeline.calls[0][0], "fromTo");
  assert.equal(timeline.calls[0][2].motionPath.end, 0);
  assert.equal(timeline.calls[0][3].motionPath.path, "#route");
  assert.equal(timeline.calls[0][3].motionPath.autoRotate, true);
  assert.equal(timeline.calls[0][3].immediateRender, true);
  assert.equal(timeline.calls[0][4], 1.2);
  assert.equal(end, 2);
});

test("custom ease profile keeps an explicit named definition", () => {
  const profile = createCustomEaseProfile({
    name: "editorial-soft-out",
    path: "M0,0 C0.14,0.72 0.24,1 1,1"
  });

  assert.deepEqual(profile, {
    name: "editorial-soft-out",
    path: "M0,0 C0.14,0.72 0.24,1 1,1"
  });
  assert.throws(() => createCustomEaseProfile({ name: "", path: "M0,0" }), /missing name/);
});

test("draw SVG transition uses explicit segment endpoints", () => {
  const timeline = fakeTimeline();
  const end = addDrawSvgTransition(timeline, {
    target: {},
    from: "50% 50%",
    to: "0% 100%",
    start: 1.4,
    duration: 0.6,
    ease: "editorial-soft-out"
  });

  assert.equal(timeline.calls[0][0], "fromTo");
  assert.equal(timeline.calls[0][2].drawSVG, "50% 50%");
  assert.equal(timeline.calls[0][3].drawSVG, "0% 100%");
  assert.equal(timeline.calls[0][3].ease, "editorial-soft-out");
  assert.equal(end, 2);
});

test("draw SVG transition rejects live length recalculation", () => {
  assert.throws(() => addDrawSvgTransition(fakeTimeline(), {
    target: {},
    to: "0% 100% live"
  }), /cannot use live DrawSVG recalculation/);
});

test("morph SVG transition carries explicit shapes and mapping options", () => {
  const timeline = fakeTimeline();
  const end = addMorphSvgTransition(timeline, {
    target: {},
    fromShape: "#circle",
    toShape: "#check",
    start: 2,
    duration: 0.8,
    morphOptions: { shapeIndex: 3, map: "position", precision: 4 }
  });

  assert.equal(timeline.calls[0][0], "fromTo");
  assert.deepEqual(timeline.calls[0][2].morphSVG, {
    shape: "#circle",
    map: "position",
    shapeIndex: 3,
    precision: 4
  });
  assert.deepEqual(timeline.calls[0][3].morphSVG, {
    shape: "#check",
    map: "position",
    shapeIndex: 3,
    precision: 4
  });
  assert.equal(end, 2.8);
});

test("text replacement uses explicit TextPlugin endpoints", () => {
  const timeline = fakeTimeline();
  const end = addTextReplacementTransition(timeline, {
    target: {},
    fromText: "旧标签",
    toText: "新标签",
    textOptions: { delimiter: "", rtl: false },
    start: 0.8,
    duration: 0.6
  });

  assert.equal(timeline.calls[0][0], "fromTo");
  assert.deepEqual(timeline.calls[0][2].text, {
    value: "旧标签",
    delimiter: "",
    rtl: false
  });
  assert.deepEqual(timeline.calls[0][3].text, {
    value: "新标签",
    delimiter: "",
    rtl: false
  });
  assert.equal(timeline.calls[0][3].ease, "none");
  assert.equal(end, 1.4);
});

test("text plugin config rejects runtime randomness", () => {
  assert.deepEqual(createTextPluginConfig("完成", { delimiter: " " }), {
    value: "完成",
    delimiter: " "
  });
  assert.throws(() => createTextPluginConfig("完成", { type: "random" }), /cannot use random values/);
});

test("map pan and pin keeps camera and label states explicit", () => {
  const timeline = fakeTimeline();
  const end = addMapPanAndPin(timeline, {
    map: {},
    pin: {},
    label: {},
    detail: {},
    highlight: {},
    mapFrom: { x: 0, y: 0, scale: 1 },
    mapTo: { x: -80, y: -30, scale: 1.08 },
    start: 0.5,
    mapDuration: 1.2
  });

  assert.deepEqual(timeline.calls.map(([method]) => method), ["fromTo", "fromTo", "fromTo", "fromTo", "fromTo"]);
  assert.deepEqual(timeline.calls[0][2], { x: 0, y: 0, scale: 1 });
  assert.deepEqual(timeline.calls[0][3].x, -80);
  assert.ok(Math.abs(timeline.calls[1][4] - 0.82) < Number.EPSILON * 4);
  assert.equal(end, 1.7);
  assert.throws(() => addMapPanAndPin(fakeTimeline(), {
    map: {},
    pin: {},
    mapFrom: { left: 0 },
    mapTo: { x: 0 }
  }), /cannot animate left/);
});

test("model compare card composes selection rail and readable name swap", () => {
  const timeline = fakeTimeline();
  const end = addModelCompareCard(timeline, {
    previousItem: {},
    nextItem: {},
    previousPanel: {},
    nextPanel: {},
    modelNameTarget: {},
    fromModelName: "旧模型",
    toModelName: "新模型",
    start: 2
  });

  assert.deepEqual(timeline.calls.map(([method]) => method), ["to", "fromTo", "to", "fromTo", "fromTo"]);
  assert.equal(timeline.calls[4][3].text.value, "新模型");
  assert.equal(timeline.calls[4][4], 2.08);
  assert.equal(end, 2.48);
});

test("evidence hold reserves a readable pause on the same timeline", () => {
  const timeline = fakeTimeline();
  const end = addEvidenceHold(timeline, {
    target: {},
    from: { y: 24, autoAlpha: 0 },
    to: { y: 0, autoAlpha: 1 },
    start: 0.4,
    enterDuration: 0.3,
    holdDuration: 1.1,
    exitDuration: 0.2
  });

  assert.deepEqual(timeline.calls.map(([method]) => method), ["fromTo", "to"]);
  assert.equal(timeline.calls[1][3], 1.8);
  assert.equal(timeline.calls[1][2].autoAlpha, 0);
  assert.equal(end, 2);
  assert.throws(() => addEvidenceHold(fakeTimeline(), {
    target: {},
    from: { left: 0 },
    to: { autoAlpha: 1 },
    holdDuration: 1
  }), /cannot animate left/);
  assert.throws(() => addEvidenceHold(fakeTimeline(), {
    target: {},
    from: { autoAlpha: 0 },
    to: { autoAlpha: 1 }
  }), /missing holdDuration/);
});

test("custom bounce and wiggle profiles are explicit and non-random", () => {
  const bounce = createCustomBounceProfile({ name: "editorial-bounce", strength: 0.55, squash: 2 });
  const wiggle = createCustomWiggleProfile({ name: "editorial-wiggle", wiggles: 5, type: "anticipate" });

  assert.deepEqual(bounce.options, {
    strength: 0.55,
    squash: 2,
    endAtStart: false,
    squashID: "editorial-bounce-squash"
  });
  assert.deepEqual(wiggle.options, { wiggles: 5, type: "anticipate" });
  assert.throws(() => createCustomWiggleProfile({ name: "bad", type: "random" }), /not seek-safe/);
});

test("setup-time numeric utilities are deterministic", () => {
  assert.equal(mapRange(0, 100, 10, 20, 25), 12.5);
  assert.equal(normalizeRange(10, 20, 15), 0.5);
  assert.equal(snapValue(10, 26), 30);
  assert.equal(snapValue([0, 10, 30], 24), 30);
  assert.deepEqual(precomputeDistributedValues({ count: 5, base: 0, amount: 1, from: "center" }), [1, 0.5, 0, 0.5, 1]);
});

test("physics 2D transition has explicit fixed parameters", () => {
  const timeline = fakeTimeline();
  const end = addPhysics2DTransition(timeline, {
    target: {},
    from: { x: 0, y: -120, rotation: -5 },
    physics2D: { velocity: 260, angle: 82, gravity: 460 },
    start: 1,
    duration: 1.4
  });

  assert.equal(timeline.calls[0][0], "fromTo");
  assert.deepEqual(timeline.calls[0][2], { x: 0, y: -120, rotation: -5 });
  assert.deepEqual(timeline.calls[0][3].physics2D, { velocity: 260, angle: 82, gravity: 460 });
  assert.equal(timeline.calls[0][3].ease, "none");
  assert.equal(end, 2.4);
});

test("physics props rejects layout properties", () => {
  assert.throws(() => addPhysicsPropsTransition(fakeTimeline(), {
    target: {},
    physicsProps: { left: { velocity: 100 } }
  }), /cannot animate left/);
});

test("physics props and tactile landing stay on one timeline", () => {
  const timeline = fakeTimeline();
  addPhysicsPropsTransition(timeline, {
    target: {},
    from: { x: 0, rotation: 0 },
    physicsProps: {
      x: { velocity: 140, acceleration: -20 },
      rotation: { velocity: 90, friction: 0.02 }
    },
    duration: 0.9
  });
  const end = addTactileLanding(timeline, {
    target: {},
    from: { y: -100, scaleX: 1, scaleY: 1 },
    bounceEase: "editorial-bounce",
    squashEase: "editorial-bounce-squash",
    start: 1,
    duration: 1.1
  });

  assert.deepEqual(timeline.calls.map(([method]) => method), ["fromTo", "fromTo", "to"]);
  assert.equal(timeline.calls[1][3].ease, "editorial-bounce");
  assert.equal(timeline.calls[2][2].ease, "editorial-bounce-squash");
  assert.equal(end, 2.1);
});
