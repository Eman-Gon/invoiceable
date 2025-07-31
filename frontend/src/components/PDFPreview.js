import React, { useState } from 'react';
import { X, ZoomIn, ZoomOut, RotateCw } from 'lucide-react';

const PDFPreview = ({ invoice, onClose }) => {
  const [scale, setScale] = useState(1.0);
  const [rotation, setRotation] = useState(0);

  const handleZoomIn = () => {
    setScale(prev => Math.min(prev + 0.2, 3.0));
  };

  const handleZoomOut = () => {
    setScale(prev => Math.max(prev - 0.2, 0.5));
  };

  const handleRotate = () => {
    setRotation(prev => (prev + 90) % 360);
  };

  // Create a blob URL for the file preview
  const createBlobUrl = () => {
    if (invoice.rawText) {
      // For text preview, create a formatted display
      return null;
    }
    // For actual PDF preview, you'd use the file blob here
    return null;
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-5xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              {invoice.fileName}
            </h2>
            <p className="text-sm text-gray-500">
              Extracted with {invoice.confidence}% confidence
            </p>
          </div>
          
          <div className="flex items-center space-x-2">
            {/* Preview Controls */}
            <div className="flex items-center space-x-1 mr-4">
              <button
                onClick={handleZoomOut}
                className="p-2 text-gray-400 hover:text-gray-600 rounded"
                title="Zoom Out"
              >
                <ZoomOut className="h-4 w-4" />
              </button>
              <span className="text-sm text-gray-600 px-2">
                {Math.round(scale * 100)}%
              </span>
              <button
                onClick={handleZoomIn}
                className="p-2 text-gray-400 hover:text-gray-600 rounded"
                title="Zoom In"
              >
                <ZoomIn className="h-4 w-4" />
              </button>
              <button
                onClick={handleRotate}
                className="p-2 text-gray-400 hover:text-gray-600 rounded ml-2"
                title="Rotate"
              >
                <RotateCw className="h-4 w-4" />
              </button>
            </div>
            
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600 rounded-lg"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex h-[calc(90vh-100px)]">
          {/* Raw Text Preview */}
          <div className="w-1/2 border-r border-gray-200 overflow-y-auto p-4">
            <h3 className="text-sm font-medium text-gray-900 mb-3">Extracted Text</h3>
            <div className="bg-gray-50 rounded-lg p-4">
              <pre className="text-xs text-gray-700 whitespace-pre-wrap font-mono">
                {invoice.rawText || 'No raw text available'}
              </pre>
            </div>
          </div>

          {/* Structured Data Preview */}
          <div className="w-1/2 overflow-y-auto p-4">
            <h3 className="text-sm font-medium text-gray-900 mb-3">Structured Data</h3>
            
            {invoice.data ? (
              <div className="space-y-4">
                {/* Basic Info */}
                <div className="bg-blue-50 rounded-lg p-4">
                  <h4 className="font-medium text-blue-900 mb-2">Invoice Information</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-blue-700">Vendor:</span>
                      <span className="font-medium">{invoice.data.vendor_name}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-blue-700">Invoice #:</span>
                      <span className="font-medium">{invoice.data.invoice_number}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-blue-700">Date:</span>
                      <span className="font-medium">{invoice.data.date}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-blue-700">Total:</span>
                      <span className="font-medium text-green-600">
                        ${invoice.data.total_amount?.toFixed(2) || '0.00'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Line Items */}
                {invoice.data.line_items && invoice.data.line_items.length > 0 && (
                  <div className="bg-green-50 rounded-lg p-4">
                    <h4 className="font-medium text-green-900 mb-2">Line Items</h4>
                    <div className="space-y-2">
                      {invoice.data.line_items.map((item, index) => (
                        <div key={index} className="text-sm border-b border-green-200 pb-2 last:border-b-0">
                          <div className="font-medium text-green-900">{item.description}</div>
                          <div className="flex justify-between text-green-700 mt-1">
                            <span>Qty: {item.quantity}</span>
                            <span>Unit: ${item.unit_price?.toFixed(2) || '0.00'}</span>
                            <span className="font-medium">Total: ${item.total?.toFixed(2) || '0.00'}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Payment Terms */}
                {invoice.data.payment_terms && (
                  <div className="bg-yellow-50 rounded-lg p-4">
                    <h4 className="font-medium text-yellow-900 mb-2">Payment Terms</h4>
                    <p className="text-sm text-yellow-800">{invoice.data.payment_terms}</p>
                  </div>
                )}

                {/* Validation Results */}
                {invoice.validation && (
                  <div className="bg-purple-50 rounded-lg p-4">
                    <h4 className="font-medium text-purple-900 mb-2">AI Validation</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-purple-700">Valid:</span>
                        <span className={`font-medium ${
                          invoice.validation.is_valid ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {invoice.validation.is_valid ? 'Yes' : 'No'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-purple-700">Confidence:</span>
                        <span className="font-medium">{(invoice.validation.confidence_score * 100).toFixed(1)}%</span>
                      </div>
                      
                      {invoice.validation.suggestions && invoice.validation.suggestions.length > 0 && (
                        <div className="mt-3">
                          <div className="text-purple-700 mb-1">Suggestions:</div>
                          <ul className="list-disc list-inside space-y-1 text-purple-600">
                            {invoice.validation.suggestions.map((suggestion, index) => (
                              <li key={index} className="text-xs">{suggestion}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center text-gray-500 py-8">
                No structured data available
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PDFPreview; 