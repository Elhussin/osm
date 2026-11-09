// scripts/fixSchemas.ts
import fs from "fs";
import path from "path";

const schemaFile = path.resolve("src/shared/api/schemas.ts");
let content = fs.readFileSync(schemaFile, "utf-8");

// استبدال z.instanceof(File) بـ z.custom<File>().refine(...)
content = content.replace(
  /z\.instanceof\(File\)/g,
  `z.custom<File>().refine(f => f instanceof File, { message: "Must be a File" })`
);

fs.writeFileSync(schemaFile, content);
console.log("✅ schemas.ts تم تعديل File بنجاح");
// bun run tsx scripts/fixSchemas.ts
// # أو
// node scripts/fixSchemas.ts
