import { expect, test, type Page } from '@playwright/test'

// Backend real contra el GIS falso: vía sintética del caso de control de OSP (SPEC-11, SPEC-B14).
const controlSegment = '/mapa?a=25.771778,-80.263610&b=25.782147,-80.264005'
const controlPoint = '/mapa?p=25.771778,-80.263610'
const fakeGisCalls = 'http://127.0.0.1:8792/_fake/calls'

const panel = (page: Page) => page.getByRole('complementary', { name: 'Resultados del mapa' })
const field = (page: Page, label: string) => panel(page).locator('.map-field', { hasText: label })
// La app escribe la URL con URLSearchParams (la coma sale como %2C): se compara ya decodificada.
const param = (page: Page, name: string) => new URL(page.url()).searchParams.get(name)

// Teselas y cualquier servicio externo bloqueados: la prueba sólo habla con 127.0.0.1 (CA-08).
test.beforeEach(async ({ page }) => {
  await page.route(/^https?:\/\/(?!127\.0\.0\.1[:/])/, (route) => route.abort())
})

test('el tramo de control por URL da la fila para OSP y resalta la vía (CA-02, CA-05)', async ({
  page,
  request,
}) => {
  await page.goto(controlSegment)
  await expect(page.getByRole('button', { name: 'Tramo' })).toHaveAttribute('aria-pressed', 'true')
  await expect(field(page, 'State Road ID')).toContainText('87281000')
  await expect(field(page, 'County')).toContainText('Miami-Dade')
  await expect(field(page, 'Section Number')).toContainText('281')
  await expect(field(page, 'Beginning Milepost')).toContainText('3.124')
  await expect(field(page, 'Ending Milepost')).toContainText('3.839')
  await expect(page.locator('path.map-line')).toBeVisible()
  expect([param(page, 'a'), param(page, 'b')]).toEqual(['25.771778,-80.263610', '25.782147,-80.264005'])
  const calls: { authorization: boolean }[] = await (await request.get(fakeGisCalls)).json()
  expect(calls.length).toBeGreaterThan(0)
  expect(calls.some((call) => call.authorization)).toBe(false)
})

test('los clics en el mapa consultan el punto: fuera y sobre la vía (CA-01, CA-08)', async ({ page }) => {
  await page.goto(controlPoint)
  await expect(panel(page).getByText('SR 953')).toBeVisible()
  await expect(field(page, 'Milepost')).toContainText('3.124')
  await expect(panel(page).getByText('FDOT (Estado de Florida)')).toBeVisible()
  await expect(field(page, 'Condado')).toContainText('Miami-Dade')
  await expect(panel(page).getByText(/Sin parcela en este punto/)).toBeVisible()
  // El marcador lo dibuja Leaflet en el punto exacto; un clic no mueve la vista.
  const marker = await page.locator('path.map-marker').boundingBox()
  const onRoad = { x: marker!.x + marker!.width / 2, y: marker!.y + marker!.height / 2 }
  await page.mouse.click(onRoad.x + 200, onRoad.y)
  await expect(panel(page).getByText(/No hay una vía a menos de 25 m/)).toBeVisible()
  await expect(field(page, 'Propietario (tasador)')).toContainText('PROPIETARIO SINTETICO 1')
  expect(param(page, 'p')).not.toBe('25.771778,-80.263610')
  await page.mouse.click(onRoad.x, onRoad.y)
  await expect(field(page, 'Milepost')).toContainText(/3\.12\d/)
})

test('el buscador lleva a una ruta con milepost y a una calle', async ({ page }) => {
  await page.goto('/mapa')
  const search = page.getByRole('combobox', { name: 'Buscar lugar' })
  await search.fill('SR 953 3.5')
  await page.getByRole('option', { name: /SR 953 · MP 3\.500/ }).click()
  await expect(field(page, 'Milepost')).toContainText(/3\.(499|500|501)/)
  expect(param(page, 'p')).toMatch(/^25\.77\d+,-80\.26\d+$/)
  await search.fill('NW 42nd Avenue')
  await search.press('ArrowDown')
  await expect(page.getByRole('option', { name: /LEJEUNE RD\/NW 42 AVE/ })).toBeVisible()
})

test('a 320 px no hay desborde horizontal y el panel queda debajo del mapa (CA-09)', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 640 })
  await page.goto(controlSegment)
  await expect(field(page, 'State Road ID')).toContainText('87281000')
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  )
  expect(overflow).toBe(0)
  const map = await page.getByRole('application', { name: 'Mapa' }).boundingBox()
  const results = await panel(page).boundingBox()
  expect(results!.y).toBeGreaterThanOrEqual(map!.y + map!.height - 1)
})

test('las opciones de vista piden la ortofoto NAIP y las vías del FDOT por área (PEN-31)', async ({
  page,
}) => {
  await page.goto(controlPoint)
  await expect(field(page, 'Milepost')).toContainText('3.124')
  await expect(page.locator('.leaflet-control-scale-line')).toHaveCount(2)
  const naip = page.waitForRequest(/USGSNAIPPlus\/ImageServer\/exportImage\?/)
  await page.getByLabel('Mapa base').selectOption('hd')
  const [minX, minY, maxX, maxY] = new URL((await naip).url()).searchParams
    .get('bbox')!
    .split(',')
    .map(Number)
  expect(maxX - minX).toBeGreaterThan(0)
  expect(maxX - minX).toBeCloseTo(maxY - minY, 1)
  const roads = page.waitForRequest(
    (request) =>
      request.url().includes('RCI_Layers/MapServer/export') && request.url().includes('dynamicLayers='),
  )
  await page.getByLabel('Vías del FDOT').check()
  await roads
  await expect(page.locator('.map-legend')).toContainText('estatales')
  await page.reload()
  await expect(page.getByLabel('Mapa base')).toHaveValue('hd')
  await expect(page.getByLabel('Vías del FDOT')).toBeChecked()
})
