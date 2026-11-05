import fs from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {FileBlob, SpreadsheetFile} from '@oai/artifact-tool';
const base=fileURLToPath(new URL('../',import.meta.url));
const out=process.env.TERRA_AMENDMENT_OUTPUT || fileURLToPath(new URL('../../source_verification_20261011_01/',import.meta.url));
const changes=JSON.parse(await fs.readFile(out+'approved_source_wording_changes.json','utf8'));
for (const author of [1,2]) {
 const w=await SpreadsheetFile.importXlsx(await FileBlob.load(base+`COMPLETED/ASSESSMENT_AUTHOR_${author}_COMPLETED.xlsx`));
 const s=w.worksheets.getItem('Assessments');
 const edits=changes.filter(c=>c.author===author);
 if(!edits.length) continue;
 for(const c of edits){
  if(s.getRange(`A${c.row}`).values[0][0]!==c.id) throw Error('ID mismatch');
  if(s.getRange(`N${c.row}`).values[0][0]!==c.old) throw Error('Original excerpt mismatch');
 }
 const r=`A${edits[0].row}:Q${edits[0].row}`;
 console.log((await w.inspect({kind:'region',sheetId:'Assessments',range:r,maxChars:800})).ndjson);
 if(process.argv.includes('--render-only')) console.log(w.help('workbook.render',{include:'examples,notes',maxChars:3500}).ndjson);
 const before=await w.render({sheetName:'Assessments',range:r,scale:1,format:'png'});
 await fs.writeFile(out+`author${author}_before.png`,new Uint8Array(await before.arrayBuffer()));
 if(process.argv.includes('--render-only')) continue;
 for(const c of edits)s.getRange(`N${c.row}`).values=[[c.replacement]];
 w.recalculate();
 const after=await w.render({sheetName:'Assessments',range:r,scale:1,format:'png'});
 await fs.writeFile(out+`author${author}_after.png`,new Uint8Array(await after.arrayBuffer()));
 const f=await SpreadsheetFile.exportXlsx(w);
 await f.save(out+`ASSESSMENT_AUTHOR_${author}_SOURCE_CORRECTED.xlsx`);
 console.log(`Author ${author}: ${edits.length} Column N changes exported`);
}
