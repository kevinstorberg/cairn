import type { ComponentType } from "react";

export interface FeatureDefinition {
  name: string;
  label: string;
  path: string;
  Component: ComponentType;
}

interface FeatureModule {
  default: FeatureDefinition;
}

type FeatureModules = Record<string, FeatureModule>;

const modules = import.meta.glob<FeatureModule>("./*/feature.tsx", { eager: true });

export const features = collectFeatures(modules);

export function collectFeatures(featureModules: FeatureModules): FeatureDefinition[] {
  return Object.values(featureModules)
    .map((module) => module.default)
    .sort((left, right) => left.label.localeCompare(right.label));
}
