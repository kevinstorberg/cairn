import "@testing-library/jest-dom/vitest";
import { beforeEach } from "vitest";

const storage = new Map<string, string>();

const localStorageShim: Storage = {
  get length() {
    return storage.size;
  },
  clear() {
    storage.clear();
  },
  getItem(key: string) {
    return storage.get(key) ?? null;
  },
  key(index: number) {
    return Array.from(storage.keys())[index] ?? null;
  },
  removeItem(key: string) {
    storage.delete(key);
  },
  setItem(key: string, value: string) {
    storage.set(key, value);
  },
};

Object.defineProperty(globalThis, "localStorage", {
  configurable: true,
  value: localStorageShim,
});

beforeEach(() => {
  localStorage.clear();
});
