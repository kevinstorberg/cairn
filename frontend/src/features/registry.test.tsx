import { describe, expect, it } from "vitest";

import { collectFeatures } from "./registry";

function Placeholder() {
  return <div />;
}

describe("feature registry", () => {
  it("collects and sorts feature modules", () => {
    const features = collectFeatures({
      "./tasks/feature.tsx": {
        default: { Component: Placeholder, label: "Tasks", name: "tasks", path: "/tasks" },
      },
      "./projects/feature.tsx": {
        default: { Component: Placeholder, label: "Projects", name: "projects", path: "/projects" },
      },
    });

    expect(features.map((feature) => feature.name)).toEqual(["projects", "tasks"]);
  });
});
