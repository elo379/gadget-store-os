"use client";

import { Dispatch, SetStateAction, useEffect, useState } from "react";
import { readStorage, writeStorage } from "@/lib/storage";

export function usePersistedState<T>(
  key: string,
  initialValue: T,
): [T, Dispatch<SetStateAction<T>>] {
  const [value, setValue] = useState<T>(() =>
    readStorage(key, initialValue),
  );

  useEffect(() => {
    writeStorage(key, value);
  }, [key, value]);

  return [value, setValue];
}
