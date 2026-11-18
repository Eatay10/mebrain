import type { Schemas } from "../api/hooks";

type TeamLike = Pick<Schemas["Team"], "id" | "name" | "unitId" | "unitName">;
const NO_UNIT = "Unit'e bağlı olmayan ekipler";

/**
 * Ekip <option>'larını bağlı oldukları unit'in altında (<optgroup>) listeler.
 * Tek bir unit varsa ya da hiçbir ekip unit'e bağlı değilse düz liste döner.
 */
export function TeamOptions({ teams }: { teams: TeamLike[] | undefined }) {
  const list = teams ?? [];
  const groups = new Map<string, TeamLike[]>();
  for (const t of list) {
    const key = t.unitName ?? NO_UNIT;
    groups.set(key, [...(groups.get(key) ?? []), t]);
  }
  const option = (t: TeamLike) => (
    <option key={t.id} value={t.id}>
      {t.name}
    </option>
  );
  if (groups.size <= 1) return <>{list.map(option)}</>;
  const names = [...groups.keys()].sort((a, b) => (a === NO_UNIT ? 1 : b === NO_UNIT ? -1 : a.localeCompare(b, "tr")));
  return (
    <>
      {names.map((n) => (
        <optgroup key={n} label={n}>
          {groups.get(n)!.sort((a, b) => a.name.localeCompare(b.name, "tr")).map(option)}
        </optgroup>
      ))}
    </>
  );
}
