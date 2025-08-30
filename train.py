from ultralytics import YOLO

def main():
    # 定义模型路径和数据集路径
    data_path = r'C:\Users\R\Desktop\Project\Anaconda\object\OVERWATCH\dataset\data.yaml'

    # 加载预训练模型
    model = YOLO("yolo11s.pt")  # load a pretrained model (recommended for training)

    # 打印模型和数据集路径，确保路径正确
    print(f"使用的数据集配置文件路径: {data_path}")

    # 开始训练
    results = model.train(
        data=data_path,  # 数据集配置文件路径
        epochs=50,  # 训练轮数
        batch=48,  # 每批次训练的样本数量
        imgsz=640,  # 输入图像的大小
        device='cuda'  # 指定训练设备，'cuda' 表示使用 GPU
    )

    # 训练完成后打印提示信息
    print("训练完成")

if __name__ == '__main__':
    main()




# from ultralytics import YOLO

# # Load a model
# model = YOLO("yolo11n-pose.yaml")  # build a new model from YAML
# model = YOLO("yolo11n-pose.pt")  # load a pretrained model (recommended for training)
# data_path = r'C:\Users\R\Desktop\Project\Anaconda\object\YoloV11_Seg\coco8-pose\data.yaml'

# # Train the model
# results = model.train(data=data_path, epochs=100, imgsz=640)