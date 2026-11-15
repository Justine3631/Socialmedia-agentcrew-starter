/**
 * Seek-safe GSAP helpers for editorial UI motion.
 * Pass the active paused timeline; helpers never create or play timelines.
 */

const requireValue = (value, name) => {
  if (value === undefined || value === null || value === "") {
    throw new Error(`editorial-motion: missing ${name}`);
  }
  return value;
};

const forbiddenLayoutProperties = new Set([
  "width", "height", "top", "right", "bottom", "left",
  "margin", "marginTop", "marginRight", "marginBottom", "marginLeft",
  "padding", "paddingTop", "paddingRight", "paddingBottom", "paddingLeft",
  "display", "visibility"
]);

const assertSeekSafeState = (state, name) => {
  requireValue(state, name);
  for (const property of Object.keys(state)) {
    if (forbiddenLayoutProperties.has(property)) {
      throw new Error(`editorial-motion: ${name} cannot animate ${property}`);
    }
  }
  return state;
};

const assertDeterministicStagger = (stagger) => {
  if (stagger === undefined) return;
  if (typeof stagger === "number") return;
  if (!stagger || typeof stagger !== "object") {
    throw new Error("editorial-motion: stagger must be a number or object");
  }
  if (stagger.from === "random") {
    throw new Error("editorial-motion: random stagger is not seek-safe");
  }
};

const assertEaseValue = (value, name) => {
  requireValue(value, name);
  if (typeof value !== "string") {
    throw new Error(`editorial-motion: ${name} must be a string`);
  }
  if (!value.trim()) {
    throw new Error(`editorial-motion: ${name} must not be empty`);
  }
  return value;
};

const assertTextValue = (value, name) => {
  if (typeof value !== "string") {
    throw new Error(`editorial-motion: ${name} must be a string`);
  }
  return value;
};

const assertDrawValue = (value, name) => {
  requireValue(value, name);
  if (typeof value !== "string" && typeof value !== "number" && typeof value !== "boolean") {
    throw new Error(`editorial-motion: ${name} must be a DrawSVG value`);
  }
  if (typeof value === "string" && /\blive\b/i.test(value)) {
    throw new Error(`editorial-motion: ${name} cannot use live DrawSVG recalculation`);
  }
  return value;
};

const assertFiniteNumber = (value, name) => {
  requireValue(value, name);
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new Error(`editorial-motion: ${name} must be a finite number`);
  }
  return value;
};

const assertNonNegativeDuration = (value, name) => {
  const duration = assertFiniteNumber(value, name);
  if (duration < 0) {
    throw new Error(`editorial-motion: ${name} must not be negative`);
  }
  return duration;
};

const assertDeterministicConfig = (config, name) => {
  requireValue(config, name);
  if (!config || typeof config !== "object" || Array.isArray(config)) {
    throw new Error(`editorial-motion: ${name} must be an object`);
  }
  for (const [key, value] of Object.entries(config)) {
    if (typeof value === "function") {
      throw new Error(`editorial-motion: ${name}.${key} cannot be a function`);
    }
    if (typeof value === "number") {
      assertFiniteNumber(value, `${name}.${key}`);
    } else if (typeof value === "string" && /random/i.test(value)) {
      throw new Error(`editorial-motion: ${name}.${key} cannot use random values`);
    } else if (value && typeof value === "object") {
      assertDeterministicConfig(value, `${name}.${key}`);
    }
  }
  return config;
};

const createMorphConfig = (shape, options = {}) => ({
  shape: requireValue(shape, "shape"),
  ...(options.map === undefined ? {} : { map: options.map }),
  ...(options.shapeIndex === undefined ? {} : { shapeIndex: options.shapeIndex }),
  ...(options.smooth === undefined ? {} : { smooth: options.smooth }),
  ...(options.curveMode === undefined ? {} : { curveMode: options.curveMode }),
  ...(options.type === undefined ? {} : { type: options.type }),
  ...(options.origin === undefined ? {} : { origin: options.origin }),
  ...(options.precision === undefined ? {} : { precision: options.precision })
});

const createTextConfig = (value, options = {}) => {
  const config = {
    value: assertTextValue(value, "text.value"),
    ...(options.delimiter === undefined ? {} : { delimiter: options.delimiter }),
    ...(options.newClass === undefined ? {} : { newClass: options.newClass }),
    ...(options.oldClass === undefined ? {} : { oldClass: options.oldClass }),
    ...(options.padSpace === undefined ? {} : { padSpace: options.padSpace }),
    ...(options.preserveSpaces === undefined ? {} : { preserveSpaces: options.preserveSpaces }),
    ...(options.rtl === undefined ? {} : { rtl: options.rtl }),
    ...(options.speed === undefined ? {} : { speed: options.speed }),
    ...(options.type === undefined ? {} : { type: options.type })
  };
  assertDeterministicConfig(config, "text");
  if (config.delimiter !== undefined && typeof config.delimiter !== "string") {
    throw new Error("editorial-motion: text.delimiter must be a string");
  }
  if (config.speed !== undefined && (typeof config.speed !== "number" || config.speed <= 0)) {
    throw new Error("editorial-motion: text.speed must be positive");
  }
  if (config.rtl !== undefined && typeof config.rtl !== "boolean") {
    throw new Error("editorial-motion: text.rtl must be boolean");
  }
  return Object.freeze(config);
};

/** Return a deterministic TextPlugin config; the composition registers TextPlugin. */
export const createTextPluginConfig = (value, options = {}) => createTextConfig(value, options);

/**
 * Return a named CustomEase definition for the composition to register once.
 * This helper does not import/register the plugin or create a second clock.
 */
export const createCustomEaseProfile = (options) => {
  const name = assertEaseValue(options?.name, "name");
  const path = assertEaseValue(options?.path, "path");
  return Object.freeze({ name, path });
};

/**
 * Return a named CustomBounce definition for the composition to register once.
 * CustomBounce also creates a companion squash ease when squash is non-zero.
 */
export const createCustomBounceProfile = (options) => {
  const name = assertEaseValue(options?.name, "name");
  const strength = assertFiniteNumber(options?.strength ?? 0.7, "strength");
  const squash = assertFiniteNumber(options?.squash ?? 0, "squash");
  const endAtStart = options?.endAtStart ?? false;
  if (strength < 0 || strength > 1) {
    throw new Error("editorial-motion: strength must be between 0 and 1");
  }
  if (squash < 0) {
    throw new Error("editorial-motion: squash must not be negative");
  }
  if (typeof endAtStart !== "boolean") {
    throw new Error("editorial-motion: endAtStart must be boolean");
  }
  const squashID = options?.squashID === undefined
    ? `${name}-squash`
    : assertEaseValue(options.squashID, "squashID");
  return Object.freeze({
    name,
    options: Object.freeze({ strength, squash, endAtStart, squashID })
  });
};

/** Return a named CustomWiggle definition without its random preset. */
export const createCustomWiggleProfile = (options) => {
  const name = assertEaseValue(options?.name, "name");
  const wiggles = assertFiniteNumber(options?.wiggles ?? 6, "wiggles");
  const type = options?.type ?? "easeOut";
  const allowedTypes = new Set(["easeOut", "easeInOut", "anticipate", "uniform"]);
  if (!Number.isInteger(wiggles) || wiggles < 1) {
    throw new Error("editorial-motion: wiggles must be a positive integer");
  }
  if (!allowedTypes.has(type)) {
    throw new Error("editorial-motion: CustomWiggle random type is not seek-safe");
  }
  return Object.freeze({
    name,
    options: Object.freeze({ wiggles, type })
  });
};

/**
 * Deterministic setup-time equivalents for the GSAP utils most useful to video.
 * Compute values before the timeline is built; do not call these per frame.
 */
export const mapRange = (inMin, inMax, outMin, outMax, value) => {
  assertFiniteNumber(inMin, "inMin");
  assertFiniteNumber(inMax, "inMax");
  assertFiniteNumber(outMin, "outMin");
  assertFiniteNumber(outMax, "outMax");
  assertFiniteNumber(value, "value");
  if (inMin === inMax) {
    throw new Error("editorial-motion: input range must not be zero");
  }
  return outMin + ((value - inMin) / (inMax - inMin)) * (outMax - outMin);
};

export const normalizeRange = (min, max, value) => mapRange(min, max, 0, 1, value);

export const snapValue = (snapTo, value) => {
  assertFiniteNumber(value, "value");
  if (Array.isArray(snapTo)) {
    if (snapTo.length === 0) {
      throw new Error("editorial-motion: snap values must not be empty");
    }
    const candidates = snapTo.map((candidate, index) => assertFiniteNumber(candidate, `snapTo[${index}]`));
    return candidates.reduce((nearest, candidate) => (
      Math.abs(candidate - value) < Math.abs(nearest - value) ? candidate : nearest
    ));
  }
  const increment = assertFiniteNumber(snapTo, "snapTo");
  if (increment <= 0) {
    throw new Error("editorial-motion: snapTo must be positive");
  }
  return Math.round(value / increment) * increment;
};

export const precomputeDistributedValues = (options) => {
  const count = options?.count;
  if (!Number.isInteger(count) || count < 1) {
    throw new Error("editorial-motion: count must be a positive integer");
  }
  const base = assertFiniteNumber(options?.base ?? 0, "base");
  const amount = assertFiniteNumber(options?.amount ?? 1, "amount");
  const from = options?.from ?? "start";
  const allowedFrom = new Set(["start", "end", "center", "edges"]);
  if (!allowedFrom.has(from)) {
    throw new Error("editorial-motion: distribution source must be start, end, center, or edges");
  }
  const denominator = Math.max(1, count - 1);
  const center = (count - 1) / 2;
  const maxDistance = Math.max(1, Math.max(center, count - 1 - center));
  return Array.from({ length: count }, (_, index) => {
    const t = index / denominator;
    const weight = from === "start"
      ? t
      : from === "end"
        ? 1 - t
        : from === "center"
          ? Math.abs(index - center) / maxDistance
          : Math.min(index, count - 1 - index) / maxDistance;
    return base + amount * weight;
  });
};

export const addThreeStageFrame = (timeline, options) => {
  const corners = requireValue(options.corners, "corners");
  const scan = requireValue(options.scan, "scan");
  const frame = requireValue(options.frame, "frame");
  const binding = requireValue(options.binding, "binding");
  const slots = requireValue(options.slots, "slots");
  const start = options.start ?? 0;
  const detect = options.detectDuration ?? 0.54;
  const frameDuration = options.frameDuration ?? 0.56;
  const lock = options.lockDuration ?? 0.50;

  timeline.to(corners, {
    autoAlpha: 1,
    duration: Math.min(0.20, detect * 0.45),
    stagger: options.cornerStagger ?? 0.045,
    ease: "power2.out"
  }, start);
  timeline.to(scan, {
    autoAlpha: options.scanOpacity ?? 0.88,
    y: options.scanTravel ?? 186,
    duration: detect - 0.08,
    ease: "power2.inOut"
  }, start + 0.02);
  timeline.to(scan, { autoAlpha: 0, duration: 0.08 }, start + detect - 0.08);
  timeline.to(corners, { autoAlpha: 0, duration: 0.12 }, start + detect);
  timeline.to(frame, {
    autoAlpha: 1,
    scaleX: 1,
    duration: frameDuration,
    ease: "power2.inOut"
  }, start + detect);
  timeline.to(frame, {
    scaleX: options.lockedFrameScaleX ?? 0.008,
    x: options.lockedFrameX ?? -42,
    duration: lock,
    ease: "power3.inOut"
  }, start + detect + frameDuration);
  timeline.to(binding, {
    autoAlpha: 1,
    scaleY: 1,
    duration: Math.max(0.20, lock - 0.08),
    ease: "power3.out"
  }, start + detect + frameDuration + 0.02);
  timeline.to(slots, {
    autoAlpha: 1,
    y: 0,
    duration: Math.max(0.20, lock - 0.14),
    stagger: options.slotStagger ?? 0.065,
    ease: "power3.out"
  }, start + detect + frameDuration + 0.05);

  return start + detect + frameDuration + lock;
};

export const addDelayedLabel = (timeline, options) => {
  const fps = options.fps ?? 30;
  const delayFrames = options.delayFrames ?? 5;
  const subjectStart = requireValue(options.subjectStart, "subjectStart");

  timeline.to(requireValue(options.subject, "subject"), {
    autoAlpha: 1,
    x: options.subjectX ?? 0,
    y: options.subjectY ?? 0,
    scale: options.subjectScale ?? 1,
    duration: options.subjectDuration ?? 0.72,
    ease: options.subjectEase ?? "power4.out"
  }, subjectStart);
  timeline.to(requireValue(options.label, "label"), {
    autoAlpha: 1,
    x: options.labelX ?? 0,
    y: options.labelY ?? 0,
    duration: options.labelDuration ?? 0.30,
    ease: options.labelEase ?? "power3.out"
  }, subjectStart + delayFrames / fps);

  return subjectStart + delayFrames / fps;
};

export const addMatchCut = (timeline, options) => {
  const cut = requireValue(options.cut, "cut");
  const fromScene = requireValue(options.fromScene, "fromScene");
  const toScene = requireValue(options.toScene, "toScene");
  const subject = requireValue(options.toSubject, "toSubject");
  const state = requireValue(options.matchState, "matchState");

  timeline.set(fromScene, { autoAlpha: 0 }, cut);
  timeline.set(toScene, { autoAlpha: 1 }, cut);
  timeline.fromTo(subject, state.from, {
    ...state.to,
    duration: options.continuationDuration ?? 2 / (options.fps ?? 30),
    ease: "none"
  }, cut);

  return cut;
};

export const addSemanticCollapse = (timeline, options) => {
  const start = options.start ?? 0;
  timeline.to(requireValue(options.source, "source"), {
    autoAlpha: 0,
    x: options.sourceExitX ?? -80,
    duration: options.sourceDuration ?? 0.30,
    ease: "power2.in"
  }, start);
  timeline.to(requireValue(options.connector, "connector"), {
    scaleX: options.connectorScaleX ?? 0.28,
    duration: options.connectorDuration ?? 0.28,
    ease: "power2.inOut"
  }, start + (options.connectorOffset ?? 0.26));
  timeline.to(requireValue(options.result, "result"), {
    autoAlpha: 0,
    clipPath: options.resultClip ?? "inset(0 48% 0 48%)",
    duration: options.resultDuration ?? 0.12,
    ease: "power2.in"
  }, start + (options.resultOffset ?? 0.46));
  timeline.to(requireValue(options.symbol, "symbol"), {
    autoAlpha: 1,
    scale: 1,
    duration: options.symbolDuration ?? 0.18,
    ease: "power3.out"
  }, start + (options.symbolOffset ?? 0.68));
};

export const addKeywordEmphasis = (timeline, options) => {
  const target = requireValue(options.target, "target");
  const marker = requireValue(options.marker, "marker");
  const start = options.start ?? 0;
  const targetDuration = options.targetDuration ?? 0.20;

  timeline.to(target, {
    color: options.color ?? "#c96332",
    duration: targetDuration,
    ease: options.targetEase ?? "power2.out"
  }, start);
  timeline.fromTo(marker, {
    scaleX: 0,
    transformOrigin: options.transformOrigin ?? "left center"
  }, {
    scaleX: 1,
    duration: options.markerDuration ?? 0.32,
    ease: options.markerEase ?? "power3.out"
  }, start + (options.markerOffset ?? 0.08));

  return start + Math.max(targetDuration, (options.markerOffset ?? 0.08) + (options.markerDuration ?? 0.32));
};

export const addCountUp = (timeline, options) => {
  const target = requireValue(options.target, "target");
  const start = options.start ?? 0;
  const from = options.from ?? 0;
  const to = requireValue(options.to, "to");
  const decimals = options.decimals ?? 0;
  const formatter = options.formatter ?? ((value) => Number(value).toFixed(decimals));
  const state = { value: from };

  timeline.set(target, { textContent: formatter(from) }, start);
  timeline.fromTo(state, { value: from }, {
    value: to,
    duration: options.duration ?? 0.72,
    ease: options.ease ?? "power3.out",
    onUpdate: () => {
      target.textContent = formatter(state.value);
    }
  }, start);

  return start + (options.duration ?? 0.72);
};

export const addFlowPath = (timeline, options) => {
  const path = requireValue(options.path, "path");
  const start = options.start ?? 0;
  const duration = options.duration ?? 0.76;
  const length = options.length ?? path.getTotalLength();

  timeline.set(path, {
    strokeDasharray: length,
    strokeDashoffset: length
  }, start);
  timeline.to(path, {
    strokeDashoffset: 0,
    duration,
    ease: options.ease ?? "power2.inOut"
  }, start);

  if (options.nodes) {
    timeline.to(options.nodes, {
      autoAlpha: 1,
      scale: 1,
      duration: options.nodeDuration ?? 0.20,
      stagger: options.nodeStagger ?? 0.10,
      ease: options.nodeEase ?? "power3.out"
    }, start + (options.nodeOffset ?? duration * 0.35));
  }

  return start + duration;
};

/**
 * Reveal caller-prepared text units through a mask-safe, deterministic cascade.
 * The caller owns text splitting and DOM structure; this helper only schedules motion.
 */
export const addMaskedTextCascade = (timeline, options) => {
  const targets = requireValue(options.targets, "targets");
  const start = options.start ?? 0;
  const duration = options.duration ?? 0.48;
  const stagger = options.stagger ?? { each: 0.055, from: "start" };
  assertDeterministicStagger(stagger);

  const from = assertSeekSafeState(options.from ?? {
    y: options.fromY ?? 28,
    autoAlpha: 0,
    rotation: options.fromRotation ?? 0
  }, "from");
  const to = assertSeekSafeState(options.to ?? {
    y: 0,
    autoAlpha: 1,
    rotation: 0
  }, "to");

  timeline.fromTo(targets, from, {
    ...to,
    duration,
    stagger,
    ease: options.ease ?? "power3.out",
    immediateRender: options.immediateRender ?? true
  }, start);

  const targetCount = options.targetCount ?? targets.length ?? 1;
  const staggerSpan = typeof stagger === "number"
    ? stagger * Math.max(0, targetCount - 1)
    : stagger.amount ?? (stagger.each ?? 0) * Math.max(0, targetCount - 1);
  return start + duration + Math.abs(staggerSpan);
};

/**
 * Switch a game-like option rail: demote the old choice, promote the new choice,
 * and replace the associated detail panel on one supplied timeline.
 */
export const addSelectionRail = (timeline, options) => {
  const previousItem = requireValue(options.previousItem, "previousItem");
  const nextItem = requireValue(options.nextItem, "nextItem");
  const previousPanel = requireValue(options.previousPanel, "previousPanel");
  const nextPanel = requireValue(options.nextPanel, "nextPanel");
  const start = options.start ?? 0;
  const itemDuration = options.itemDuration ?? 0.32;
  const itemOffset = options.itemOffset ?? 0;
  const panelDuration = options.panelDuration ?? 0.38;
  const panelExitDuration = options.panelExitDuration ?? panelDuration * 0.72;
  const panelOffset = options.panelOffset ?? 0.10;
  const itemStart = start + itemOffset;

  timeline.to(previousItem, {
    scale: options.previousScale ?? 0.94,
    autoAlpha: options.previousAlpha ?? 0.56,
    duration: itemDuration,
    ease: options.itemEase ?? "power3.out"
  }, itemStart);
  timeline.fromTo(nextItem, {
    scale: options.nextFromScale ?? 0.94,
    autoAlpha: options.nextFromAlpha ?? 0.70
  }, {
    scale: options.nextScale ?? 1,
    autoAlpha: 1,
    duration: itemDuration,
    ease: options.itemEase ?? "power3.out",
    immediateRender: false
  }, itemStart);
  timeline.to(previousPanel, {
    x: options.panelExitX ?? -18,
    autoAlpha: 0,
    duration: panelExitDuration,
    ease: options.panelExitEase ?? "power2.in"
  }, start);
  timeline.fromTo(nextPanel, {
    x: options.panelEnterX ?? 24,
    autoAlpha: 0
  }, {
    x: 0,
    autoAlpha: 1,
    duration: panelDuration,
    ease: options.panelEase ?? "power3.out",
    immediateRender: false
  }, start + panelOffset);

  return start + Math.max(itemOffset + itemDuration, panelExitDuration, panelOffset + panelDuration);
};

/**
 * FLIP-style shared-state movement without runtime measurement or DOM mutation.
 * Geometry is precomputed by the caller and supplied as explicit transform states.
 */
export const addExplicitStateTransition = (timeline, options) => {
  const target = requireValue(options.target, "target");
  const from = assertSeekSafeState(requireValue(options.from, "from"), "from");
  const to = assertSeekSafeState(requireValue(options.to, "to"), "to");
  const start = options.start ?? 0;
  const duration = options.duration ?? 0.62;

  timeline.fromTo(target, from, {
    ...to,
    duration,
    ease: options.ease ?? "power3.inOut",
    immediateRender: options.immediateRender ?? false
  }, start);

  return start + duration;
};

/**
 * Add a MotionPathPlugin tween without importing or registering the plugin.
 * The composition must load and register MotionPathPlugin before calling this helper.
 */
export const addMotionPathFollower = (timeline, options) => {
  const target = requireValue(options.target, "target");
  const path = requireValue(options.path, "path");
  const align = requireValue(options.align, "align");
  const start = options.start ?? 0;
  const duration = options.duration ?? 0.9;
  const alignOrigin = options.alignOrigin ?? [0.5, 0.5];
  const autoRotate = options.autoRotate ?? false;
  const pathStart = options.pathStart ?? 0;
  const pathEnd = options.pathEnd ?? 1;

  timeline.fromTo(target, {
    motionPath: {
      path,
      align,
      alignOrigin,
      autoRotate,
      start: pathStart,
      end: pathStart
    }
  }, {
    motionPath: {
      path,
      align,
      alignOrigin,
      autoRotate,
      start: pathStart,
      end: pathEnd
    },
    duration,
    ease: options.ease ?? "power2.inOut",
    immediateRender: options.immediateRender ?? true
  }, start);

  return start + duration;
};

/**
 * Draw an SVG stroke between explicit segments with DrawSVGPlugin.
 * The composition must load and register DrawSVGPlugin before calling this helper.
 */
export const addDrawSvgTransition = (timeline, options) => {
  const target = requireValue(options.target, "target");
  const from = assertDrawValue(options.from ?? "0% 0%", "from");
  const to = assertDrawValue(options.to ?? "0% 100%", "to");
  const start = options.start ?? 0;
  const duration = options.duration ?? 0.76;

  timeline.fromTo(target, { drawSVG: from }, {
    drawSVG: to,
    duration,
    ease: options.ease ?? "power2.inOut",
    immediateRender: options.immediateRender ?? true
  }, start);

  return start + duration;
};

/**
 * Morph one explicit SVG shape into another with MorphSVGPlugin.
 * Shapes may be selectors, SVG elements, or raw path data; the composition
 * must load and register MorphSVGPlugin before calling this helper.
 */
export const addMorphSvgTransition = (timeline, options) => {
  const target = requireValue(options.target, "target");
  const fromShape = requireValue(options.fromShape, "fromShape");
  const toShape = requireValue(options.toShape, "toShape");
  const start = options.start ?? 0;
  const duration = options.duration ?? 0.72;
  const morphOptions = options.morphOptions ?? {};

  timeline.fromTo(target, {
    morphSVG: createMorphConfig(fromShape, morphOptions)
  }, {
    morphSVG: createMorphConfig(toShape, morphOptions),
    duration,
    ease: options.ease ?? "power2.inOut",
    immediateRender: options.immediateRender ?? true
  }, start);

  return start + duration;
};

/** Replace readable text through TextPlugin on the caller's paused timeline. */
export const addTextReplacementTransition = (timeline, options) => {
  const target = requireValue(options.target, "target");
  const fromText = assertTextValue(options.fromText ?? "", "fromText");
  const toText = assertTextValue(options.toText ?? "", "toText");
  const start = options.start ?? 0;
  const duration = options.duration ?? 0.72;
  const textOptions = options.textOptions ?? {};

  timeline.fromTo(target, {
    text: createTextConfig(fromText, textOptions)
  }, {
    text: createTextConfig(toText, textOptions),
    duration,
    ease: "none",
    immediateRender: options.immediateRender ?? true
  }, start);

  return start + duration;
};

/**
 * Pan a pre-positioned map and reveal one point of interest in a fixed order.
 * Camera and pin geometry are supplied explicitly; no layout measurement is used.
 */
export const addMapPanAndPin = (timeline, options) => {
  const map = requireValue(options.map, "map");
  const pin = requireValue(options.pin, "pin");
  const mapFrom = assertSeekSafeState(requireValue(options.mapFrom, "mapFrom"), "mapFrom");
  const mapTo = assertSeekSafeState(requireValue(options.mapTo, "mapTo"), "mapTo");
  const pinFrom = assertSeekSafeState(options.pinFrom ?? {
    y: -18,
    scale: 0.86,
    autoAlpha: 0
  }, "pinFrom");
  const pinTo = assertSeekSafeState(options.pinTo ?? {
    y: 0,
    scale: 1,
    autoAlpha: 1
  }, "pinTo");
  const start = options.start ?? 0;
  const mapDuration = options.mapDuration ?? 1.20;
  const pinOffset = options.pinOffset ?? 0.32;
  const pinDuration = options.pinDuration ?? 0.34;

  timeline.fromTo(map, mapFrom, {
    ...mapTo,
    duration: mapDuration,
    ease: options.mapEase ?? "power1.inOut",
    immediateRender: options.immediateRender ?? true
  }, start);
  timeline.fromTo(pin, pinFrom, {
    ...pinTo,
    duration: pinDuration,
    ease: options.pinEase ?? "power3.out",
    immediateRender: false
  }, start + pinOffset);

  let end = Math.max(start + mapDuration, start + pinOffset + pinDuration);
  if (options.label !== undefined) {
    const label = requireValue(options.label, "label");
    const labelFrom = assertSeekSafeState(options.labelFrom ?? {
      y: 12,
      autoAlpha: 0
    }, "labelFrom");
    const labelTo = assertSeekSafeState(options.labelTo ?? {
      y: 0,
      autoAlpha: 1
    }, "labelTo");
    const labelOffset = options.labelOffset ?? pinOffset + 0.16;
    const labelDuration = options.labelDuration ?? 0.28;
    timeline.fromTo(label, labelFrom, {
      ...labelTo,
      duration: labelDuration,
      ease: options.labelEase ?? "power3.out",
      immediateRender: false
    }, start + labelOffset);
    end = Math.max(end, start + labelOffset + labelDuration);
  }

  if (options.detail !== undefined) {
    const detail = requireValue(options.detail, "detail");
    const detailFrom = assertSeekSafeState(options.detailFrom ?? {
      y: 16,
      autoAlpha: 0
    }, "detailFrom");
    const detailTo = assertSeekSafeState(options.detailTo ?? {
      y: 0,
      autoAlpha: 1
    }, "detailTo");
    const detailOffset = options.detailOffset ?? pinOffset + 0.34;
    const detailDuration = options.detailDuration ?? 0.32;
    timeline.fromTo(detail, detailFrom, {
      ...detailTo,
      duration: detailDuration,
      ease: options.detailEase ?? "power3.out",
      immediateRender: false
    }, start + detailOffset);
    end = Math.max(end, start + detailOffset + detailDuration);
  }

  if (options.highlight !== undefined) {
    const highlight = requireValue(options.highlight, "highlight");
    const highlightFrom = assertSeekSafeState(options.highlightFrom ?? {
      scale: 0.82,
      autoAlpha: 0
    }, "highlightFrom");
    const highlightTo = assertSeekSafeState(options.highlightTo ?? {
      scale: 1,
      autoAlpha: 1
    }, "highlightTo");
    const highlightOffset = options.highlightOffset ?? pinOffset + 0.42;
    const highlightDuration = options.highlightDuration ?? 0.24;
    timeline.fromTo(highlight, highlightFrom, {
      ...highlightTo,
      duration: highlightDuration,
      ease: options.highlightEase ?? "back.out(1.4)",
      immediateRender: false
    }, start + highlightOffset);
    end = Math.max(end, start + highlightOffset + highlightDuration);
  }

  return end;
};

/**
 * Compose a model-comparison card from the selection rail plus one readable name swap.
 * The card's feature rows remain caller-owned DOM so the helper does not invent copy.
 */
export const addModelCompareCard = (timeline, options) => {
  const start = options.start ?? 0;
  let end = addSelectionRail(timeline, options);

  if (options.modelNameTarget !== undefined) {
    const modelNameTarget = requireValue(options.modelNameTarget, "modelNameTarget");
    const fromModelName = assertTextValue(options.fromModelName, "fromModelName");
    const toModelName = assertTextValue(options.toModelName, "toModelName");
    end = Math.max(end, addTextReplacementTransition(timeline, {
      target: modelNameTarget,
      fromText: fromModelName,
      toText: toModelName,
      textOptions: options.modelNameTextOptions ?? { delimiter: "" },
      start: options.modelNameStart ?? start + 0.08,
      duration: options.modelNameDuration ?? 0.34,
      immediateRender: false
    }));
  }

  return end;
};

/**
 * Reveal an evidence card, reserve a deliberate reading pause, then optionally
 * leave it. The hold is a real gap on the supplied timeline, not a timer.
 */
export const addEvidenceHold = (timeline, options) => {
  const target = requireValue(options.target, "target");
  const from = assertSeekSafeState(requireValue(options.from, "from"), "from");
  const to = assertSeekSafeState(requireValue(options.to, "to"), "to");
  const start = options.start ?? 0;
  const enterDuration = assertNonNegativeDuration(options.enterDuration ?? 0.36, "enterDuration");
  const holdDuration = assertNonNegativeDuration(requireValue(options.holdDuration, "holdDuration"), "holdDuration");
  const exitDuration = assertNonNegativeDuration(options.exitDuration ?? 0, "exitDuration");

  timeline.fromTo(target, from, {
    ...to,
    duration: enterDuration,
    ease: options.enterEase ?? "power3.out",
    immediateRender: options.immediateRender ?? true
  }, start);

  const holdEnd = start + enterDuration + holdDuration;
  if (exitDuration > 0) {
    const exitTo = assertSeekSafeState(options.exitTo ?? { autoAlpha: 0 }, "exitTo");
    timeline.to(target, {
      ...exitTo,
      duration: exitDuration,
      ease: options.exitEase ?? "power2.in",
      immediateRender: false
    }, holdEnd);
  }

  return holdEnd + exitDuration;
};

/**
 * Add a fixed-parameter Physics2DPlugin move. The plugin must be registered by
 * the composition; the helper supplies explicit x/y state and no wall clock.
 */
export const addPhysics2DTransition = (timeline, options) => {
  const target = requireValue(options.target, "target");
  const from = assertSeekSafeState(options.from ?? { x: 0, y: 0 }, "from");
  const physics2D = assertDeterministicConfig(requireValue(options.physics2D, "physics2D"), "physics2D");
  assertFiniteNumber(physics2D.velocity, "physics2D.velocity");
  assertFiniteNumber(physics2D.angle, "physics2D.angle");
  const start = options.start ?? 0;
  const duration = options.duration ?? 1.2;

  timeline.fromTo(target, from, {
    physics2D,
    duration,
    ease: "none",
    immediateRender: options.immediateRender ?? true
  }, start);

  return start + duration;
};

/**
 * Add fixed-parameter PhysicsPropsPlugin motion for numeric properties such as
 * x/y/rotation. Layout properties remain forbidden by the HyperFrames contract.
 */
export const addPhysicsPropsTransition = (timeline, options) => {
  const target = requireValue(options.target, "target");
  const from = assertSeekSafeState(options.from ?? {}, "from");
  const physicsProps = assertDeterministicConfig(requireValue(options.physicsProps, "physicsProps"), "physicsProps");
  for (const property of Object.keys(physicsProps)) {
    if (forbiddenLayoutProperties.has(property)) {
      throw new Error(`editorial-motion: physicsProps cannot animate ${property}`);
    }
  }
  const start = options.start ?? 0;
  const duration = options.duration ?? 1.2;

  timeline.fromTo(target, from, {
    physicsProps,
    duration,
    ease: "none",
    immediateRender: options.immediateRender ?? true
  }, start);

  return start + duration;
};

/**
 * A restrained bounce landing: one subject, one fixed position ease, and an
 * optional companion squash ease created by CustomBounce.
 */
export const addTactileLanding = (timeline, options) => {
  const target = requireValue(options.target, "target");
  const from = assertSeekSafeState(requireValue(options.from, "from"), "from");
  const bounceEase = assertEaseValue(options.bounceEase, "bounceEase");
  const start = options.start ?? 0;
  const duration = options.duration ?? 1.2;
  const landingY = options.landingY ?? 0;

  timeline.fromTo(target, from, {
    y: landingY,
    duration,
    ease: bounceEase,
    immediateRender: options.immediateRender ?? true
  }, start);

  if (options.squashEase !== undefined) {
    const squashEase = assertEaseValue(options.squashEase, "squashEase");
    timeline.to(target, {
      scaleX: options.squashScaleX ?? 1.08,
      scaleY: options.squashScaleY ?? 0.92,
      duration,
      ease: squashEase,
      transformOrigin: options.transformOrigin ?? "center bottom",
      immediateRender: false
    }, start);
  }

  return start + duration;
};
