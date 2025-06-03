// world_map.js — Tile-based world map engine for Kingmaker's Rise
import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm';


const canvas = document.getElementById('world-canvas');
const ctx = canvas.getContext('2d');

let zoom = 1;
let offsetX = 0;
let offsetY = 0;
let isDragging = false;
let dragStart = { x: 0, y: 0 };

const TILE_SIZE = 32;
const VIEW_RADIUS = 100;
const TERRAIN_COLORS = {
  plains: '#c2b280',
  forest: '#228b22',
  desert: '#edc9af',
  mountain: '#555555',
  water: '#4a90e2',
  snow: '#dfefff',
  swamp: '#556b2f',
  volcanic: '#b22222',
  unknown: '#cccccc'
};

window.addEventListener('DOMContentLoaded', async () => {
  await renderVisibleTiles();
  bindControls();
});

function bindControls() {
  document.getElementById('zoom-in').addEventListener('click', () => { zoom = Math.min(zoom * 1.25, 10); renderVisibleTiles(); });
  document.getElementById('zoom-out').addEventListener('click', () => { zoom = Math.max(zoom / 1.25, 0.1); renderVisibleTiles(); });
  document.getElementById('center-map').addEventListener('click', () => { offsetX = 0; offsetY = 0; renderVisibleTiles(); });

  canvas.addEventListener('mousedown', (e) => {
    isDragging = true;
    dragStart.x = e.clientX;
    dragStart.y = e.clientY;
  });

  canvas.addEventListener('mouseup', () => { isDragging = false; });
  canvas.addEventListener('mouseleave', () => { isDragging = false; });

  canvas.addEventListener('mousemove', (e) => {
    if (!isDragging) return;
    offsetX += (e.clientX - dragStart.x) / zoom;
    offsetY += (e.clientY - dragStart.y) / zoom;
    dragStart.x = e.clientX;
    dragStart.y = e.clientY;
    renderVisibleTiles();
  });

  canvas.addEventListener('wheel', (e) => {
    e.preventDefault();
    zoom *= e.deltaY < 0 ? 1.1 : 0.9;
    zoom = Math.max(0.1, Math.min(zoom, 10));
    renderVisibleTiles();
  });

  document.getElementById('logout-btn').addEventListener('click', async () => {
    await supabase.auth.signOut();
    window.location.href = 'index.html';
  });
}

async function renderVisibleTiles() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const cols = Math.floor(canvas.width / (TILE_SIZE * zoom)) + 2;
  const rows = Math.floor(canvas.height / (TILE_SIZE * zoom)) + 2;
  const startX = Math.floor(-offsetX / TILE_SIZE) - Math.floor(cols / 2);
  const startY = Math.floor(-offsetY / TILE_SIZE) - Math.floor(rows / 2);

  const { data: tiles, error } = await supabase
    .from('world_tiles')
    .select('*')
    .gte('x', startX)
    .lte('x', startX + cols)
    .gte('y', startY)
    .lte('y', startY + rows);

  if (error) return console.error('Tile fetch failed', error);

  tiles.forEach(tile => drawTile(tile));
}

function drawTile(tile) {
  const terrain = tile.terrain_type || 'unknown';
  const color = TERRAIN_COLORS[terrain] || TERRAIN_COLORS.unknown;

  const screenX = (tile.x * TILE_SIZE + offsetX) * zoom;
  const screenY = (tile.y * TILE_SIZE + offsetY) * zoom;

  ctx.fillStyle = color;
  ctx.fillRect(screenX, screenY, TILE_SIZE * zoom, TILE_SIZE * zoom);
  ctx.strokeStyle = '#111';
  ctx.lineWidth = 0.5;
  ctx.strokeRect(screenX, screenY, TILE_SIZE * zoom, TILE_SIZE * zoom);

  if (zoom >= 2) {
    ctx.fillStyle = 'black';
    ctx.font = `${12 * zoom}px IM Fell English`;
    ctx.fillText(`${tile.x},${tile.y}`, screenX + 4, screenY + 14);
  }
}