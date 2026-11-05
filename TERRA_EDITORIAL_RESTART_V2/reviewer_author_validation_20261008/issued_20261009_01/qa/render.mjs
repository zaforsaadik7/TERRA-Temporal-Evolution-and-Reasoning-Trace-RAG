import fs from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {FileBlob, SpreadsheetFile} from '@oai/artifact-tool';
for (const author of [1,2]) {
 const w=await SpreadsheetFile.importXlsx(await FileBlob.load(fileURLToPath(new URL(`../ASSESSMENT_AUTHOR_${author}.xlsx`,import.meta.url))));
 for (const [sheet,range,tag] of [['Instructions_and_Rubric','A1:A20','instructions'],['Assessments','G1:Q3','entry'],['Detailed_Reading_View','A1:B8','reading']]) {
  const b=await w.render({sheetName:sheet,range,scale:1,format:'png'});
  await fs.writeFile(new URL(`author${author}_${tag}.png`,import.meta.url),new Uint8Array(await b.arrayBuffer()));
 }
 console.log(`Author ${author}: rendered all three sheet types`);
}
