import { rootNodeFromAnchor } from '@codama/nodes-from-anchor';
import { createFromRoot } from 'codama';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

// --- SỬA LỖI IMPORT TẠI ĐÂY ---
// Import toàn bộ package vào biến 'CodamaPyPkg' rồi mới lấy hàm ra
import CodamaPyPkg from 'codama-py';
const { renderVisitor } = CodamaPyPkg; 

// 1. Đọc file IDL
const idlContent = readFileSync(join(process.cwd(), 'oracle.json'), 'utf-8');
const idl = JSON.parse(idlContent);

// 2. Tạo Codama Root Node
const root = createFromRoot(rootNodeFromAnchor(idl));

// 3. Xuất code Python
// Lưu ý: renderVisitor thường yêu cầu tham số là (path, options)
await root.accept(
  renderVisitor('oracle_client', {
    package: { name: 'oracle_client', version: '0.1.0' },
  })
);

console.log('✅ Đã tạo xong SDK Python trong thư mục /oracle_client!');