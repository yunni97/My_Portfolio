declare module 'cornerstone-core' {
  export interface Image {
    imageId: string;
    minPixelValue: number;
    maxPixelValue: number;
    slope: number;
    intercept: number;
    windowCenter: number;
    windowWidth: number;
    render: any;
    getPixelData: () => Uint8Array | Int16Array | Uint16Array;
    rows: number;
    columns: number;
    height: number;
    width: number;
    color: boolean;
    columnPixelSpacing: number;
    rowPixelSpacing: number;
    sizeInBytes: number;
  }

  export interface Viewport {
    scale: number;
    translation: { x: number; y: number };
    voi: { windowWidth: number; windowCenter: number };
    invert: boolean;
    pixelReplication: boolean;
    rotation: number;
    hflip: boolean;
    vflip: boolean;
    modalityLUT?: any;
    voiLUT?: any;
    colormap?: any;
  }

  export function enable(element: HTMLElement): void;
  export function disable(element: HTMLElement): void;
  export function displayImage(element: HTMLElement, image: Image, viewport?: Viewport): void;
  export function loadImage(imageId: string): Promise<Image>;
  export function getViewport(element: HTMLElement): Viewport;
  export function setViewport(element: HTMLElement, viewport: Viewport): void;
  export function getDefaultViewportForImage(element: HTMLElement, image: Image): Viewport;
  export function reset(element: HTMLElement): void;
  export function resize(element: HTMLElement, forcedResize?: boolean): void;
}

declare module 'cornerstone-wado-image-loader' {
  export const external: {
    cornerstone: any;
    dicomParser: any;
  };

  export interface WadoImageLoaderConfig {
    beforeSend?: (xhr: XMLHttpRequest) => void;
    useWebWorkers?: boolean;
    webWorkerPath?: string;
    taskConfiguration?: any;
    decodeConfig?: any;
  }

  export function configure(config: WadoImageLoaderConfig): void;
  export function loadImage(imageId: string): Promise<any>;
}

declare module 'dicom-parser' {
  export function parseDicom(byteArray: Uint8Array, options?: any): any;
  export function readEncapsulatedPixelData(dataSet: any, pixelDataElement: any, frame: number): any;
}
