/**
 * export Service 测试
 */

import {
  exportLotToIFC,
  exportProjectToIFC,
  batchExportLotsToIFC,
  downloadBlob,
} from '../export'
import { ApiError } from '../api'

// Mock global fetch
global.fetch = jest.fn()
const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>

// Mock URL.createObjectURL and document.createElement
global.URL.createObjectURL = jest.fn(() => 'blob:mock-url')
global.URL.revokeObjectURL = jest.fn()

describe('export Service', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('exportLotToIFC', () => {
    it('应该成功导出检验批为IFC', async () => {
      const mockBlob = new Blob(['IFC content'], { type: 'application/octet-stream' })
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        blob: async () => mockBlob,
      } as Response)
      
      const result = await exportLotToIFC('lot-1')
      
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/export/ifc?inspection_lot_id=lot-1'),
        expect.objectContaining({
          method: 'GET',
        })
      )
      expect(result).toBeInstanceOf(Blob)
    })

    it('应该在导出失败时抛出错误', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 404,
        statusText: 'Not Found',
        json: async () => ({ detail: 'Lot not found' }),
      } as Response)
      
      await expect(exportLotToIFC('nonexistent')).rejects.toThrow('Lot not found')
    })
  })

  describe('exportProjectToIFC', () => {
    it('应该成功导出项目为IFC', async () => {
      const mockBlob = new Blob(['IFC content'])
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        blob: async () => mockBlob,
      } as Response)
      
      const result = await exportProjectToIFC('project-1')
      
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/export/ifc?project_id=project-1'),
        expect.objectContaining({
          method: 'GET',
        })
      )
      expect(result).toBeInstanceOf(Blob)
    })
  })

  describe('batchExportLotsToIFC', () => {
    it('应该成功批量导出检验批为IFC', async () => {
      const mockBlob = new Blob(['IFC content'])
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        blob: async () => mockBlob,
      } as Response)
      
      const result = await batchExportLotsToIFC(['lot-1', 'lot-2'])
      
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/export/ifc/batch'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ lot_ids: ['lot-1', 'lot-2'] }),
        })
      )
      expect(result).toBeInstanceOf(Blob)
    })
  })

  describe('downloadBlob', () => {
    it('应该创建下载链接并触发下载', () => {
      const mockBlob = new Blob(['test'])
      const mockLink = {
        href: '',
        download: '',
        click: jest.fn(),
        remove: jest.fn(),
      }
      
      const createElementSpy = jest.spyOn(document, 'createElement').mockReturnValue(mockLink as any)
      const appendChildSpy = jest.spyOn(document.body, 'appendChild').mockImplementation(() => mockLink as any)
      const removeChildSpy = jest.spyOn(document.body, 'removeChild').mockImplementation(() => mockLink as any)
      
      downloadBlob(mockBlob, 'test.ifc')
      
      expect(createElementSpy).toHaveBeenCalledWith('a')
      expect(mockLink.href).toBe('blob:mock-url')
      expect(mockLink.download).toBe('test.ifc')
      expect(appendChildSpy).toHaveBeenCalled()
      expect(mockLink.click).toHaveBeenCalled()
      expect(removeChildSpy).toHaveBeenCalled()
      expect(global.URL.revokeObjectURL).toHaveBeenCalledWith('blob:mock-url')
      
      createElementSpy.mockRestore()
      appendChildSpy.mockRestore()
      removeChildSpy.mockRestore()
    })
  })
})

