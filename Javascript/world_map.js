// Project Name: Thronestead©
// File Name: world_map.js
// Version:  7/1/2025 10:38
// Developer: Deathsgift66
// world_map.js — Tile-based world map engine for Thronestead
import { supabase } from '../supabaseClient.js';

let currentSession;
let mapChannel;

const canvas = document.getElementById('world-canvas');
const ctx = canvas?.getContext('2d');
if (!canvas || !ctx) throw new Error('world-canvas element missing');

let zoom = 1;
let offsetX = 0;
let offsetY = 0;
let isDragging = false;
let dragStart = { x: 0, y: 0 };

const TILE_SIZE = 32;
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
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    window.location.href = 'login.html';
    return;
  }
  currentSession = session;
  resizeCanvas();
  await renderVisibleTiles();
  bindRealtime();
  bindControls();
  window.addEventListener('resize', () => {
    resizeCanvas();
    renderVisibleTiles();
  });
});

window.addEventListener('beforeunload', () => {
  if (mapChannel) supabase.removeChannel(mapChannel);
});

// Adjust canvas size to viewport
function resizeCanvas() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
}

function bindControls() {
  document.getElementById('zoom-in')?.addEventListener('click', () => {
    zoom = Math.min(zoom * 1.25, 10);
    renderVisibleTiles();
  });
  document.getElementById('zoom-out')?.addEventListener('click', () => {
    zoom = Math.max(zoom / 1.25, 0.1);
    renderVisibleTiles();
  });
  document.getElementById('center-map')?.addEventListener('click', () => {
    offsetX = 0;
    offsetY = 0;
    renderVisibleTiles();
  });

  canvas.addEventListener('mousedown', (e) => {
    isDragging = true;
    dragStart.x = e.clientX;
    dragStart.y = e.clientY;
    canvas.style.cursor = 'grabbing';
  });

  canvas.addEventListener('mouseup', () => {
    isDragging = false;
    canvas.style.cursor = 'grab';
  });
  canvas.addEventListener('mouseleave', () => {
    isDragging = false;
    canvas.style.cursor = 'grab';
  });

  canvas.addEventListener('mousemove', (e) => {
    if (!isDragging) return;
    offsetX += (e.clientX - dragStart.x) / zoom;
    offsetY += (e.clientY - dragStart.y) / zoom;
    dragStart.x = e.clientX;
    dragStart.y = e.clientY;
    renderVisibleTiles();
  });

  canvas.style.cursor = 'grab';

  canvas.addEventListener('wheel', (e) => {
    e.preventDefault();
    zoom *= e.deltaY < 0 ? 1.1 : 0.9;
    zoom = Math.max(0.1, Math.min(zoom, 10));
    renderVisibleTiles();
  });


}

function bindRealtime() {
  mapChannel = supabase
    .channel('world-map')
    .on('postgres_changes', { event: '*', schema: 'public', table: 'terrain_map' }, async () => {
      await renderVisibleTiles();
    })
    .subscribe();
}

async function renderVisibleTiles() {
  if (!ctx) return;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const cols = Math.floor(canvas.width / (TILE_SIZE * zoom)) + 2;
  const rows = Math.floor(canvas.height / (TILE_SIZE * zoom)) + 2;
  const startX = Math.floor(-offsetX / TILE_SIZE) - Math.floor(cols / 2);
  const startY = Math.floor(-offsetY / TILE_SIZE) - Math.floor(rows / 2);

  try {
    const res = await fetch('/api/world-map/tiles', {
      headers: {
        'Authorization': `Bearer ${currentSession.access_token}`,
        'X-User-ID': currentSession.user.id
      }
    });
    if (!res.ok) throw new Error('Tile fetch failed');
    const mapRow = await res.json();

    const tiles = (mapRow?.tile_map?.tiles || [])
      .filter(t => t.x >= startX && t.x <= startX + cols &&
                  t.y >= startY && t.y <= startY + rows);

    tiles.forEach(drawTile);

  } catch (err) {
    console.error('Failed to render tiles:', err);
  }
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
