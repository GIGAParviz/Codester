import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = new URL("..", import.meta.url).pathname.replace(/^\//, "").replaceAll("/", "\\");
const dataPath = `${root}data\\mesc_catalog_synthetic.csv`;
const outputDir = `${root}outputs`;
const outputPath = `${outputDir}\\mesc_synthetic_catalog.xlsx`;
const csvText = (await fs.readFile(dataPath, "utf8")).replace(/^\uFEFF/, "");
const rowCount = csvText.trim().split(/\r?\n/).length;
const workbook = await Workbook.fromCSV(csvText, { sheetName: "Catalog" });
const catalog = workbook.worksheets.getItem("Catalog");
const readme = workbook.worksheets.add("README");
catalog.showGridLines = false;
readme.showGridLines = false;
catalog.getRange("A1:Y1").format = { fill: "#17365D", font: { name: "Arial", size: 10, bold: true, color: "#FFFFFF" }, horizontalAlignment: "center", verticalAlignment: "center", wrapText: true };
catalog.getRange(`A2:Y${rowCount}`).format = { font: { name: "Arial", size: 9, color: "#1F2937" }, verticalAlignment: "center" };
catalog.getRange(`D2:E${rowCount}`).format.wrapText = true;
catalog.getRange(`X2:Y${rowCount}`).format.wrapText = false;
catalog.getRange("A:Y").format.columnWidth = 16;
catalog.getRange("D:E").format.columnWidth = 42;
catalog.getRange("X:Y").format.columnWidth = 28;
catalog.getRange("A1:Y1").format.rowHeight = 30;
catalog.freezePanes.freezeRows(1);
catalog.tables.add(`A1:Y${rowCount}`, true, "SyntheticCatalog");

readme.getRange("A1:D1").values = [["MESC Copilot synthetic catalogue", "", "", ""]];
readme.mergeCells("A1:D1");
readme.getRange("A1:D1").format = { font: { name: "Arial", size: 15, bold: true, color: "#17365D" } };
readme.getRange("A3:B11").values = [
  ["Purpose", "Synthetic fixture for search, ranking and API development"],
  ["Rows", rowCount - 1],
  ["Truth status", "Not an official MESC catalogue"],
  ["Provenance", "synthetic_fixture_v1"],
  ["Canonical code shape", "XX.XX.XX.XXX.X"],
  ["Included languages", "English and Persian descriptions"],
  ["Main pilot query", "لوله دو اینچی پلاستیکی برند داچ"],
  ["Search index", "SQLite indexed table plus structured filters in scripts/search_mesc.py"],
  ["Real-data action", "Replace synthetic rows only after an approved catalogue export arrives"]
];
readme.getRange("A3:A11").format = { fill: "#D9EAF7", font: { name: "Arial", size: 10, bold: true, color: "#17365D" } };
readme.getRange("B3:B11").format = { font: { name: "Arial", size: 10, color: "#1F2937" }, wrapText: true };
readme.getRange("A:A").format.columnWidth = 24;
readme.getRange("B:B").format.columnWidth = 72;
readme.getRange("A1:D20").format.verticalAlignment = "center";

workbook.recalculate();
await fs.mkdir(outputDir, { recursive: true });
const preview = await workbook.render({ sheetName: "README", autoCrop: "all", scale: 1, format: "png" });
await fs.writeFile(`${outputDir}\\mesc_catalog_readme.png`, new Uint8Array(await preview.arrayBuffer()));
const xlsx = await SpreadsheetFile.exportXlsx(workbook);
await xlsx.save(outputPath);
const check = await workbook.inspect({ kind: "table", range: `Catalog!A1:Y6`, include: "values", tableMaxRows: 6, tableMaxCols: 25 });
console.log(check.ndjson);
console.log(outputPath);
